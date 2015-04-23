#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdarg.h>
#include <argp.h>
#ifndef NOPGPLOT
#include "cpgplot.h"
#endif

#define BUFSIZE 256
#define MAX_NANTS 6

const char *argp_program_version="atsen_commandline v1.1";
const char *argp_program_bug_address="<Jamie.Stevens@csiro.au>";

static char doc[]="ATCA CABB Sensitivity Calculator";

static struct argp_option options[]={
  {"frequency",'f',"FREQ",0,"the central frequency of the observations (MHz)"},
  {"configuration",'c',"CONFIG",0,"the array configuration"},
  {"dec",'d',"DEC",0,"the declination of the source (decimal degrees)"},
  {"ca06",'6',0,0,"include CA06 for the calculations"},
  {"integration",'t',"TIME",0,"the amount of on-source integration time (min)"},
  {"ellimit",'e',"EL_LIMIT",0,"the elevation limit to use (decimal degrees)"},
  {"halimit",'a',"HA_LIMIT",0,"the hour angle limit to use (decimal hours)"},
  {"corrconfig",'b',"CORR_CONFIG",0,"the correlator configuration"},
  {"weighting",'w',"WEIGHTING",0,"the imaging weighting scheme"},
  {"output",'o',"PLOTFILE",0,"the name of the PNG file to output the RMS v frequency spectrum to (no extension)"},
  {"html",'H',0,0,"output should be in HTML for display in webpage"},
  {"mfactor",'m',"MFACTOR",0,"specify this parameter to override the default system temperature multiplication factor"},
  {"4ghz",'4',0,0,"use a 4 GHz continuum band"},
  {"zoomfreq",'z',"ZOOMFREQ",0,"a specific zoom channel to calculate parameters for"},
  { 0 }
};


typedef struct _form {
  int frequency;
  int configuration;
  int max_baseline;
  int track_baseline;
  int hybrid;
  float dec;
  int useca06;
  float integration;
  float ellimit;
  float halimit;
  char bandwidth[BUFSIZE];
  char weight[BUFSIZE];
  int do_atm;
  float *tr;
  float *fr;
  float *tau[3];
  float mfactor;
  float mfactor_override;
  int asize;
  char output_plot[BUFSIZE];
  int html_output;
  int wide_continuum;
  int zoom_frequency;
  int specific_zoom;
} form;

#define N_CONFIGSTRINGS 18
#define N_BANDWIDTHS 4
#define N_WEIGHTS 8

static error_t parse_opt(int key,char *arg,struct argp_state *state){
  form *form=state->input;
  int i,found;
  int config_values[N_CONFIGSTRINGS]={6000,6000,3000,3000,1500,1500,750,750,367,367,367,367,
				      214,214,168,168,75,75};
  int config_hybrid[N_CONFIGSTRINGS]={0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1};
  char config_strings[N_CONFIGSTRINGS][BUFSIZE]={"6000","6km","3000","3km","1500","1.5km",
						 "750","750m","367","EW352","EW367","EW352/367",
						 "h214","H214","h168","H168","h75","H75"};
  char bandwidth[N_BANDWIDTHS][BUFSIZE]={"CFB1M","CFB4M","CFB16M","CFB64M"};
  char weights[N_WEIGHTS][BUFSIZE]={"N","R2","R1","R0","R-1","R-2","U","SU"};

  switch (key){
  case 'o':
    strcpy(form->output_plot,arg);
    break;
  case 'w':
    found=0;
    for (i=0;i<N_WEIGHTS;i++){
      if (strcmp(arg,weights[i])==0){
	found=1;
	strcpy(form->weight,weights[i]);
	break;
      }
    }
    if (found==0){
      printf("Unable to recognise imaging weighting scheme, please use one of the following "
	     "weighting strings:\n");
      for (i=0;i<N_WEIGHTS;i++){
	if (i!=0){
	  printf(", ");
	}
	printf("%s",weights[i]);
      }
    }
    break;
  case 'b':
    found=0;
    for (i=0;i<N_BANDWIDTHS;i++){
      if (strcmp(arg,bandwidth[i])==0){
	found=1;
	strcpy(form->bandwidth,bandwidth[i]);
	break;
      }
    }
    if (found==0){
      printf("Unable to recognise correlator configuration, please use one of the following "
	     "configuration strings:\n");
      for (i=0;i<N_CONFIGSTRINGS;i++){
	if (i!=0){
	  printf(", ");
	}
	printf("%s",bandwidth[i]);
      }
    }
    break;
  case 'a':
    sscanf(arg,"%f",&(form->halimit));
    break;
  case 'e':
    sscanf(arg,"%f",&(form->ellimit));
    break;
  case 't':
    sscanf(arg,"%f",&(form->integration));
    break;
  case '6':
    form->useca06=1;
    break;
  case 'd':
    sscanf(arg,"%f",&(form->dec));
    break;
  case 'f':
    sscanf(arg,"%d",&(form->frequency));
    break;
  case 'c':
    found=0;
    for (i=0;i<N_CONFIGSTRINGS;i++){
      if (strcmp(arg,config_strings[i])==0){
	form->configuration=config_values[i];
	form->hybrid=config_hybrid[i];
	found=1;
	break;
      }
    }
    if (found==0){
      /* specified a non-recognised string */
      printf("Unable to recognise configuration, please use one of the following "
	     "configuration strings:\n");
      for (i=0;i<N_CONFIGSTRINGS;i++){
	if (i!=0){
	  printf(", ");
	}
	printf("%s",config_strings[i]);
      }
      printf("\n");
    }
    break;
  case 'H':
    form->html_output=1;
    break;
  case 'm':
    sscanf(arg,"%f",&(form->mfactor_override));
    break;
  case '4':
    form->wide_continuum=1;
    break;
  case 'z':
    sscanf(arg,"%d",&(form->zoom_frequency));
    break;
  default:
    return ARGP_ERR_UNKNOWN;
  }

  return 0;
}

static struct argp argp = {options,parse_opt,NULL,doc};

typedef struct _system_temperature {
  int *chan_nchans;
  float **chan_freqs;
  int **chan_n;
  float **chan_tsys;
  float **chan_tsys_average;
  float **chan_tsys_poor;
} system_temperature;

void present_results(form *form);
float interp(int size,float *t,float *f,float freq);
void assign_weight(float *rfac,float *bfac,int configuration,
		   float *r_array,float *b_array,int *config_array,int array_size);
void read_file(char *file,float bandwidth,float chanwidth,int nchans,
	       float centrefreq,form *form,int *ants,int n_ants,system_temperature *tsys);
float calc_tsys(float halim,float ellim,float dec,float trec,float tau);
void tsys_structure(float bandwidth,float channelwidth,float centrefreq,
		    form *form,system_temperature *tsys);
void calculate_rms_array(float rfac,system_temperature *tsys,float efficiency,
			 float dishdiameter,float totalbw,float effbw,float tint,
			 int nbl,int polproductscombined,float centrefreq,
			 int *ants,int n_ants,float *otsys,float **rms_array,
			 float **freq_array,int *n_rms_array,float sz_freq,
			 float **sz_tsys);
float calc_average(float *array,int n_array);
float calculate_rms(float rfac,float tsys,float efficiency,float dishdiameter,
		    float effbw,float tint,int nbl,int polproductscombined);
void calculate_systemsens(float dishdiameter,int nantsused,float tsys,
			  float efficiency,float *ssen_single,float *ssen_all);
float calculate_btsens(float rms,float wavesq,float res1,float res2);
void minmax(float *array,int n_array,float *min,float *max);
void bt_format(float bt,char *format);

int main(int argc,char *argv[]){
  form form;

  form.configuration=6000;
  form.hybrid=0;
  form.dec=-30.0;
  form.useca06=0;
  form.integration=720;
  form.ellimit=12;
  form.halimit=6;
  form.html_output=0;
  form.mfactor_override=-1;
  strcpy(form.bandwidth,"CFB1M");
  strcpy(form.weight,"N");
  strcpy(form.output_plot,"rms_spectrum");
  form.wide_continuum=0;
  form.zoom_frequency=0;

  argp_parse(&argp,argc,argv,0,0,&form);

  strcat(form.output_plot,".png/png");

  present_results(&form);

  exit(0);
}

#define N_NAF 66
#define N_W_INFO 11
#define N_Q_INFO 21
#define N_K_INFO 20
#define N_CONFIGS 10

/* some constraints on frequency */
#define THREEMM_FREQ_LOW 83857
#define THREEMM_FREQ_HIGH 104785
#define SEVENMM_FREQ_LOW 30000
#define SEVENMM_FREQ_HIGH 50000
#define TWELVEMM_FREQ_LOW 16000
#define TWELVEMM_FREQ_HIGH 25000
#define THREECM_FREQ_LOW 8501
#define THREECM_FREQ_HIGH 9499
#define SIXCM_FREQ_LOW 5125
#define SIXCM_FREQ_HIGH 5999
#define THIRTEENCM_FREQ_LOW 1730
#define THIRTEENCM_FREQ_HIGH 2999
#define TWENTYCM_FREQ_LOW 1730
#define TWENTYCM_FREQ_HIGH 2999

#define ARRAY_FLOAT 1
#define ARRAY_INT 2
void assign_array(void *array,int type,int array_size,...){
  va_list ap;
  int i;
  int *tiarray;
  float *tfarray;
  
  if (type==ARRAY_FLOAT){
    tfarray=array;
  } else if (type==ARRAY_INT){
    tiarray=array;
  }

  va_start(ap,array_size);

  for (i=0;i<array_size;i++){
    if (type==ARRAY_FLOAT){
      tfarray[i]=(float)va_arg(ap,double);
    } else if (type==ARRAY_INT){
      tiarray[i]=(int)va_arg(ap,int);
    }
  }

  va_end(ap);
}

void present_results(form *form){
  /* frequencies (in MHz) that we have data points for */
  float efficiency,tsys[3],sbz,rfac,bfac,bw,sb;
  float rr0[N_CONFIGS],rr_1[N_CONFIGS],rr_2[N_CONFIGS],ru[N_CONFIGS],rsu[N_CONFIGS];
  float br1[N_CONFIGS],br0[N_CONFIGS],br_1[N_CONFIGS],br_2[N_CONFIGS],bu[N_CONFIGS];
  float bsu[N_CONFIGS],dishdiameter,speedoflight,radianstodegrees,degreestoarcmin;
  float metrestokilometres,mhztohz,metrestocentimetres,degreestoarcsec;
  float pbfwhm,vres,vres2,vwidth,wavesq,res1,res2,*rms_array=NULL,rms[3];
  float *freq_array=NULL,vres2s,mres1,mres2,sres1,sres2;
  float ssen_single[3],ssen_all[3],bt[3],sbrms[3],sbbt[3],sbrmsz[3],sbbtz[3];
  float sbrmszs[3],sbbtzs[3];
  float min_freq,max_freq,min_rms,max_rms,*sz_tsys=NULL,sz_rms;
  int twelvemm=0,sevenmm=0,threemm=0,nbl,nantsused,nchan,polproductscombined;
  int *usable_antenna=NULL,n_usable_antenna,n_rms_array,calcn,i,ier,ncc=3;
  char obw[BUFSIZE],weight[BUFSIZE],pb_units[BUFSIZE],outformat[3][BUFSIZE];
  char tmpformat[BUFSIZE];
  system_temperature systemp;

  sz_tsys=malloc(3*sizeof(float));
  if (sz_tsys==NULL){
    printf("unable to allocate memory!\n");
    exit (-1);
  }

  float naf[N_NAF]={1200, 1500, 1800, 2100, 2300, 2500, 4400, 5900, 7400, 8800,10600,
		    16000,16500,17000,17500,18000,18500,19000,19500,20000,20500,21000,
		    21500,22000,22500,23000,23500,24000,24500,25000,25400,
		    30000,31000,32000,33000,34000,35000,36000,37000,38000,39000,
		    40000,41000,42000,43000,44000,45000,46000,47000,48000,49000,50000,
		    83781.1, 85556.2, 86834.3, 88680.5, 90526.6, 91946.7, 94005.9,
		    95852.1, 97272.2, 98976.3,100254.4,102200.0,102300.0,106432.0};
  /* antenna efficiencies at the frequencies listed in 'naf' */
  float na[N_NAF]={0.66, 0.69, 0.62, 0.52, 0.51, 0.53, 0.65, 0.72, 0.65, 0.64, 0.65, 
		   0.58, 0.62, 0.63, 0.65, 0.67, 0.70, 0.68, 0.64, 0.64, 0.60, 0.53,
		   0.55, 0.54, 0.51, 0.51, 0.53, 0.49, 0.49, 0.46, 0.47,
		   0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60,
		   0.60, 0.59, 0.58, 0.57, 0.56, 0.55, 0.54, 0.53, 0.52, 0.51, 0.50,
		   0.3297,0.3065,0.3020,0.2856,0.2689,0.2670,0.2734,
		   0.2727,0.2521,0.2403,0.2336,0.2322,0.14,0.14};
  /* these 'w' arrays relate to the 3mm band */
  float wtr[N_W_INFO]={280.0, 255.0, 220.0, 178.0, 143.0, 140.0,     
		       150.0, 155.0, 163.0, 182.0, 192.0};
  float wf[N_W_INFO]={83857, 85785, 87571, 89714, 91857, 95071,
		      97285, 99071,101214,102928,104785};
  float wtau1[N_W_INFO]={0.140,0.136,0.134,0.133,0.134,0.137,
			 0.140,0.145,0.150,0.157,0.166};
  float wtau2[N_W_INFO]={0.173,0.171,0.171,0.172,0.174,0.180,
			 0.185,0.191,0.199,0.208,0.219};
  float wtau3[N_W_INFO]={0.220,0.221,0.222,0.226,0.231,0.240,
			 0.248,0.257,0.267,0.279,0.293};
  
  /* these 'q' arrays relate to the 7mm band */
  float qtr[N_Q_INFO]={ 40.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 
			32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0};
  float qf[N_Q_INFO]={30000,31000,32000,33000,34000,35000,36000,37000,38000,39000,
		      40000,41000,42000,43000,44000,45000,46000,47000,48000,49000,50000};
  float qtau1[N_Q_INFO]={0.040,0.041,0.042,0.044,0.047,0.050,0.053,0.057,0.062,0.067,
			 0.073,0.081,0.089,0.100,0.113,0.129,0.148,0.174,0.208,0.255,0.325};
  float qtau2[N_Q_INFO]={0.048,0.048,0.050,0.052,0.054,0.057,0.061,0.065,0.070,0.075,
			 0.082,0.089,0.099,0.110,0.123,0.139,0.160,0.186,0.221,0.270,0.342};
  float qtau3[N_Q_INFO]={0.059,0.059,0.060,0.062,0.065,0.068,0.071,0.076,0.081,0.087,
			 0.094,0.101,0.112,0.123,0.136,0.153,0.174,0.201,0.237,0.286,0.359};

  /* these 'k' arrays relate to the 12mm band */
  float ktr[N_K_INFO]={ 30.0, 25.9, 23.2, 22.0, 21.2, 21.4, 22.4, 22.9, 23.6, 22.6, 20.3,
			19.4, 19.9, 19.2, 19.1, 18.6, 17.8, 20.1, 22.7, 28.3};
  float kf[N_K_INFO]={16000,16500,17000,17500,18000,18500,19000,19500,20000,20500,21000,
		      21500,22000,22500,23000,23500,24000,24500,25000,25400};
  float ktau1[N_K_INFO]={0.017,0.018,0.019,0.021,0.023,0.026,0.030,0.034,0.040,0.047,0.056,
			 0.064,0.072,0.075,0.073,0.068,0.062,0.057,0.053,0.049};
  float ktau2[N_K_INFO]={0.019,0.021,0.023,0.025,0.029,0.033,0.037,0.044,0.052,0.062,0.074,
			 0.087,0.097,0.101,0.098,0.091,0.083,0.075,0.068,0.063};
  float ktau3[N_K_INFO]={0.023,0.025,0.028,0.032,0.036,0.041,0.048,0.057,0.069,0.083,0.101,
			 0.119,0.133,0.139,0.134,0.124,0.111,0.100,0.090,0.082};

  /* weighting factors */
  int configs[N_CONFIGS]={75,122,168,214,367,375,750,1500,3000,6000};
  float rn[N_CONFIGS]={1,1,1,1,1,1,1,1,1,1};
  float rr2[N_CONFIGS]={1,1,1,1,1,1,1,1,1,1};
  float rr1[N_CONFIGS]={1,1,1,1,1,1,1,1.01,1.01,1.01};

  float bn[N_CONFIGS]={0.77,0.95,0.75,0.74,1.09,0.97,0.96,0.96,0.97,1.32};
  float br2[N_CONFIGS]={0.77,0.95,0.75,0.74,1.09,0.97,0.96,0.96,0.97,1.32};

  if (form->hybrid==1){
    assign_array(rr0,ARRAY_FLOAT,N_CONFIGS,1.37,1.33,1.34,1.18,1.22,1.25,1.21,1.18,1.16,1.16);
    assign_array(rr_1,ARRAY_FLOAT,N_CONFIGS,1.63,1.82,2.22,1.52,1.63,1.74,1.42,1.33,1.23,1.22);
    assign_array(rr_2,ARRAY_FLOAT,N_CONFIGS,1.63,1.84,2.31,1.54,1.65,1.76,1.43,1.33,1.24,1.22);
    assign_array(ru,ARRAY_FLOAT,N_CONFIGS,1.63,1.84,2.32,1.54,1.65,1.77,1.43,1.33,1.24,1.22);
    assign_array(rsu,ARRAY_FLOAT,N_CONFIGS,3.43,4.00,1.85,1.65,1.80,1.77,1.54,1.44,1.33,1.32);
    assign_array(br1,ARRAY_FLOAT,N_CONFIGS,0.76,0.91,0.74,0.73,1.00,0.90,0.88,0.88,0.89,1.32);
    assign_array(br0,ARRAY_FLOAT,N_CONFIGS,0.58,0.61,0.61,0.64,0.68,0.62,0.62,0.64,0.66,0.84);
    assign_array(br_1,ARRAY_FLOAT,N_CONFIGS,0.53,0.55,0.59,0.62,0.64,0.58,0.59,0.62,0.64,0.80);
    assign_array(br_2,ARRAY_FLOAT,N_CONFIGS,0.53,0.55,0.59,0.62,0.64,0.58,0.59,0.62,0.64,0.80);
    assign_array(bu,ARRAY_FLOAT,N_CONFIGS,0.53,0.55,0.59,0.62,0.64,0.58,0.59,0.62,0.64,0.80);
    assign_array(bsu,ARRAY_FLOAT,N_CONFIGS,0.52,0.54,0.59,0.59,0.61,0.59,0.60,0.61,0.63,0.76);
  } else {
    assign_array(rr0,ARRAY_FLOAT,N_CONFIGS,1.37,1.33,1.34,1.17,1.22,1.25,1.21,1.18,1.16,1.16);
    assign_array(rr_1,ARRAY_FLOAT,N_CONFIGS,1.63,1.82,2.22,1.33,1.63,1.74,1.42,1.33,1.23,1.22);
    assign_array(rr_2,ARRAY_FLOAT,N_CONFIGS,1.63,1.84,2.31,1.33,1.65,1.76,1.43,1.33,1.24,1.22);
    assign_array(ru,ARRAY_FLOAT,N_CONFIGS,1.63,1.84,2.32,1.33,1.65,1.77,1.43,1.33,1.24,1.22);
    assign_array(rsu,ARRAY_FLOAT,N_CONFIGS,3.43,4.00,1.85,1.78,1.80,1.77,1.54,1.44,1.33,1.32);
    assign_array(br1,ARRAY_FLOAT,N_CONFIGS,0.76,0.91,0.74,0.91,1.00,0.90,0.88,0.88,0.89,1.32);
    assign_array(br0,ARRAY_FLOAT,N_CONFIGS,0.58,0.61,0.61,0.69,0.68,0.62,0.62,0.64,0.66,0.84);
    assign_array(br_1,ARRAY_FLOAT,N_CONFIGS,0.53,0.55,0.59,0.67,0.64,0.58,0.59,0.62,0.64,0.80);
    assign_array(br_2,ARRAY_FLOAT,N_CONFIGS,0.53,0.55,0.59,0.67,0.64,0.58,0.59,0.62,0.64,0.80);
    assign_array(bu,ARRAY_FLOAT,N_CONFIGS,0.53,0.55,0.59,0.67,0.64,0.58,0.59,0.62,0.64,0.80);
    assign_array(bsu,ARRAY_FLOAT,N_CONFIGS,0.52,0.54,0.59,0.62,0.61,0.59,0.60,0.61,0.63,0.76);
  }

  /* interpolate the antenna beam efficiency */
  efficiency=interp(N_NAF,na,naf,form->frequency);

  /* determine some parameters for later */
  form->do_atm=0;
  if ((form->frequency>=THREEMM_FREQ_LOW)&&
      (form->frequency<=THREEMM_FREQ_HIGH)){
    threemm=1;
    form->tr=wtr;
    form->fr=wf;
    form->tau[0]=wtau1;
    form->tau[1]=wtau2;
    form->tau[2]=wtau3;
    form->do_atm=1;
    form->asize=N_W_INFO;
/*     form->mfactor=2.3; */
    form->mfactor=1;
  } else if ((form->frequency>=SEVENMM_FREQ_LOW)&&
	     (form->frequency<=SEVENMM_FREQ_HIGH)){
    sevenmm=1;
    form->tr=qtr;
    form->fr=qf;
    form->tau[0]=qtau1;
    form->tau[1]=qtau2;
    form->tau[2]=qtau3;
    form->do_atm=1;
    form->asize=N_Q_INFO;
/*     form->mfactor=2.0; */
    form->mfactor=1;
  } else if ((form->frequency>=TWELVEMM_FREQ_LOW)&&
	     (form->frequency<=TWELVEMM_FREQ_HIGH)){
    twelvemm=1;
    form->tr=ktr;
    form->fr=kf;
    form->tau[0]=ktau1;
    form->tau[1]=ktau2;
    form->tau[2]=ktau3;
    form->do_atm=1;
    form->asize=N_K_INFO;
/*     form->mfactor=1.4; */
    form->mfactor=1;
  } else if ((form->frequency>=THREECM_FREQ_LOW)&&
	     (form->frequency<=THREECM_FREQ_HIGH)){
    /* we don't need to prepare anything if we're calculating for a 
       3cm frequency */
    form->do_atm=1;
    form->wide_continuum=0;
  } else if ((form->frequency>=SIXCM_FREQ_LOW)&&
	     (form->frequency<=SIXCM_FREQ_HIGH)){
    /* we don't need to prepare anything if we're calculating for a 
       3cm frequency */
    form->do_atm=1;
    form->wide_continuum=0;
  } else if ((form->frequency>=THIRTEENCM_FREQ_LOW)&&
	     (form->frequency<=THIRTEENCM_FREQ_HIGH)){
    /* currently we have a smaller bandwidth at 13cm, so we set the
       nominal centre frequency here so it cannot be changed by the user */
/*     form->frequency=2400; */
    form->wide_continuum=0;
  } else if ((form->frequency>=TWENTYCM_FREQ_LOW)&&
	     (form->frequency<=TWENTYCM_FREQ_HIGH)){
    /* currently we have a smaller bandwidth at 20cm, so we set the
       nominal centre frequency here so it cannot be changed by the user */
/*     form->frequency=1500; */
    form->wide_continuum=0;
  } else {
    printf("The central frequency you have selected is out of the valid range, "
	   "please try again\n");
    printf("Valid ranges are:\n");
    printf("20cm: %d - %d MHz\n",TWENTYCM_FREQ_LOW,TWENTYCM_FREQ_HIGH);
    printf("13cm: %d - %d MHz\n",THIRTEENCM_FREQ_LOW,THIRTEENCM_FREQ_HIGH);
    printf(" 6cm: %d - %d MHz\n",SIXCM_FREQ_LOW,SIXCM_FREQ_HIGH);
    printf(" 3cm: %d - %d MHz\n",THREECM_FREQ_LOW,THREECM_FREQ_HIGH);
    printf("12mm: %d - %d MHz\n",TWELVEMM_FREQ_LOW,TWELVEMM_FREQ_HIGH);
    printf(" 7mm: %d - %d MHz\n",SEVENMM_FREQ_LOW,SEVENMM_FREQ_HIGH);
    printf(" 3mm: %d - %d MHz\n",THREEMM_FREQ_LOW,THREEMM_FREQ_HIGH);
    exit(-1);
  }
  /* do we override the mfactor? */
  if (form->mfactor_override!=-1){
    form->mfactor=form->mfactor_override;
  }

  /* determine the number of baselines to use */
  if (threemm){
    form->useca06=0;
  }
  if (((form->configuration==6000)&&(form->useca06==1))||
      (form->useca06==1)){
    nbl=15;
    nantsused=6;
    form->max_baseline=6000;
    form->track_baseline=form->configuration;
  } else {
    nbl=10;
    nantsused=5;
    if (form->configuration==6000){
      form->max_baseline=3000;
    } else {
      form->max_baseline=form->configuration;
    }
    form->track_baseline=form->max_baseline;
  }

  /* do some error checking */
  if (((form->dec==0)&&(!form->hybrid))||
      (form->dec<-90)||(form->dec>90)||(form->integration<=0)){
    printf("Please choose declinations greater than -90 (other than zero), "
	   "and non-zero integration times.\n");
    return;
  }
  if ((form->ellimit<12)||(form->ellimit>90)||
      (form->halimit<=0)||(form->halimit>12)){
    printf("Please choose an elevation limit between 12 and 90 degrees, and "
	   "a positive, non-zero hour-angle limit less than 12 hours.\n");
  }

  /* more setup */
  if (strcmp(form->bandwidth,"CFB1M")==0){
    strcpy(obw,"CFB1M-0.5k");
    bw=2048; sb=1; nchan=2048;
  } else if (strcmp(form->bandwidth,"CFB4M")==0){
    strcpy(obw,"CFB4M-2k");
    bw=2048; sb=4; nchan=512;
  } else if (strcmp(form->bandwidth,"CFB16M")==0){
    strcpy(obw,"CFB16M-8k");
    bw=2048; sb=16; nchan=128;
  } else if (strcmp(form->bandwidth,"CFB64M")==0){
    strcpy(obw,"CFB64M-32k");
    bw=2048; sb=64; nchan=32;
  }
  if (form->wide_continuum==1){
    bw*=2; nchan*=2;
  }

  sbz=(float)sb/2048.0;

  if (strcmp(form->weight,"N")==0){
    strcpy(weight,"Natural");
    assign_weight(&rfac,&bfac,form->configuration,rn,bn,configs,N_CONFIGS);
  } else if (strcmp(form->weight,"R2")==0){
    strcpy(weight,"Robust=2");
    assign_weight(&rfac,&bfac,form->configuration,rr2,br2,configs,N_CONFIGS);
  } else if (strcmp(form->weight,"R1")==0){
    strcpy(weight,"Robust=1");
    assign_weight(&rfac,&bfac,form->configuration,rr1,br1,configs,N_CONFIGS);
  } else if (strcmp(form->weight,"R0")==0){
    strcpy(weight,"Robust=0");
    assign_weight(&rfac,&bfac,form->configuration,rr0,br0,configs,N_CONFIGS);
  } else if (strcmp(form->weight,"R-1")==0){
    strcpy(weight,"Robust=-1");
    assign_weight(&rfac,&bfac,form->configuration,rr_1,br_1,configs,N_CONFIGS);
  } else if (strcmp(form->weight,"R-2")==0){
    strcpy(weight,"Robust=-2");
    assign_weight(&rfac,&bfac,form->configuration,rr_2,br_2,configs,N_CONFIGS);
  } else if (strcmp(form->weight,"U")==0){
    strcpy(weight,"Uniform");
    assign_weight(&rfac,&bfac,form->configuration,ru,bu,configs,N_CONFIGS);
  } else if (strcmp(form->weight,"SU")==0){
    strcpy(weight,"Superuniform");
    assign_weight(&rfac,&bfac,form->configuration,rsu,bsu,configs,N_CONFIGS);
  }

  /* some constants that we need */
  dishdiameter=22.0; /* dish diameter in m */
  speedoflight=299792458.0; /* speed of light in m/s */
  radianstodegrees=180.0/3.141592654; /* conversion between radians and degrees */
  degreestoarcmin=60.0; /* conversion between degrees and arcminutes */
  metrestokilometres=1.0/1000.0; /* conversion between metres and kilometres */
  mhztohz=1e6; /* conversion between MHz and Hz */
  metrestocentimetres=100.0; /* conversion between metres and cm */
  degreestoarcsec=3600.0; /* conversion between degrees and arcseconds */

  /* check for a specific zoom frequency */
  if ((form->zoom_frequency>=(form->frequency-(bw/2)))&&
      (form->zoom_frequency<=(form->frequency+(bw/2)))){
    form->specific_zoom=1;
    ncc=4;
  } else {
    form->specific_zoom=0;
  }

  /* some simple derived quantities */
  pbfwhm=(speedoflight/dishdiameter)/(form->frequency*mhztohz)*radianstodegrees*
    degreestoarcmin;
  vres=(speedoflight*metrestokilometres)*sb/form->frequency;
  vres2=(speedoflight*metrestokilometres)*sbz/form->frequency;
  if (form->specific_zoom==1){
    vres2s=(speedoflight*metrestokilometres)*sbz/(float)form->zoom_frequency;
  }
  vwidth=(speedoflight*metrestokilometres)*bw/form->frequency;
  wavesq=powf(((speedoflight*metrestocentimetres/mhztohz)/form->frequency),2); /* in cm^2 */

  /* work out the synthesised beam size */
  res1=bfac*speedoflight/((form->frequency*mhztohz)*form->track_baseline)*
    radianstodegrees*degreestoarcsec;
  mres1=bfac*speedoflight/((form->frequency*mhztohz)*form->max_baseline)*
    radianstodegrees*degreestoarcsec;
  if (form->specific_zoom==1){
    sres1=bfac*speedoflight/((form->zoom_frequency*mhztohz)*form->track_baseline)*
      radianstodegrees*degreestoarcsec;
  }
  if (form->hybrid==1){
    res2=res1;
    mres2=mres1;
    if (form->specific_zoom==1){
      sres2=sres1;
    }
  } else {
    res2=res1/fabsf(sinf(form->dec/radianstodegrees));
    mres2=mres1/fabsf(sinf(form->dec/radianstodegrees));
    if (form->specific_zoom==1){
      sres2=sres1/fabsf(sinf(form->dec/radianstodegrees));
    }
  }

  /* the number of polarisation products we combine to get the final output;
     we choose 2 here, which is XX & YY -> Stokes I */
  polproductscombined=2;
  if (form->html_output==0){
    printf("- calculating the Tsys structure\n");
  }
  systemp.chan_freqs=NULL;
  tsys_structure(bw,sb,form->frequency,form,&systemp);
  n_usable_antenna=5;
  usable_antenna=malloc(n_usable_antenna*sizeof(int));
  assign_array(usable_antenna,ARRAY_INT,n_usable_antenna,1,2,3,4,5);
  if (nantsused==6){
    n_usable_antenna++;
    usable_antenna=realloc(usable_antenna,n_usable_antenna*sizeof(int));
    usable_antenna[n_usable_antenna-1]=6;
  }


  /* get the continuum RMS noise level for all weather conditions */
  if (form->html_output==0){
    printf("- calculating sensitivity for each channel\n");
  }
  calculate_rms_array(rfac,&systemp,efficiency,dishdiameter,bw,sb,
		      form->integration,nbl,polproductscombined,
		      form->frequency,usable_antenna,n_usable_antenna,tsys,
		      &rms_array,&freq_array,&n_rms_array,
		      (float)(form->zoom_frequency),&sz_tsys);

  calcn=1;
  if ((twelvemm==1)||(sevenmm==1)||(threemm==1)){
    calcn=3;
  }


  for (i=0;i<calcn;i++){
    rms[i]=calculate_rms(rfac,tsys[i],efficiency,dishdiameter,bw,
			 form->integration,nbl,polproductscombined);
    /* get the system sensitivity for each antenna and for all antennae combined */
    calculate_systemsens(dishdiameter,nantsused,tsys[i],efficiency,
			 &(ssen_single[i]),&(ssen_all[i]));
    bt[i]=calculate_btsens(rms[i],wavesq,res1,res2);

    if (nchan>1){
      /* calculate the spectral line RMS noise level for all weather conditions */
      sbrms[i]=calculate_rms(rfac,tsys[i],efficiency,dishdiameter,sb,
			     form->integration,nbl,polproductscombined);
      sbbt[i]=calculate_btsens(sbrms[i],wavesq,res1,res2);
      sbrmsz[i]=calculate_rms(rfac,tsys[i],efficiency,dishdiameter,sbz,
			      form->integration,nbl,polproductscombined);
      sbbtz[i]=calculate_btsens(sbrmsz[i],wavesq,res1,res2);
      if (form->specific_zoom==1){
	sbrmszs[i]=calculate_rms(rfac,sz_tsys[i],efficiency,dishdiameter,sbz,
				form->integration,nbl,polproductscombined);
	sbbtzs[i]=calculate_btsens(sbrmszs[i],wavesq,sres1,sres2);
      }
    }
  }

  /* make a plot of channel RMS noise vs frequency */
#ifdef cpgplot_h
  cpgopen(form->output_plot);
  cpgscrn(0,"white",&ier);
  cpgscrn(1,"black",&ier);
  minmax(rms_array,n_rms_array,&min_rms,&max_rms);
  minmax(freq_array,n_rms_array,&min_freq,&max_freq);
  if (min_rms==max_rms){
    min_rms*=0.9;
    max_rms*=1.1;
  }
  cpgswin(min_freq,max_freq,min_rms,max_rms);
  cpgbox("BCNTS",0.0,0,"BCNTS",0.0,0);
  cpgline(n_rms_array,freq_array,rms_array);
  cpglab("Frequency (MHz)","RMS Noise Level (mJy/beam)","");
  cpgclos();
#endif

  /* do some rounding of the figures for presentability */
  if (pbfwhm>2.0){
    strcpy(pb_units,"arcmin");
  } else {
    pbfwhm*=60.0;
    strcpy(pb_units,"arcsec");
  }

  if (form->html_output==0){
    printf("Configuration parameters:\n");
    printf("Configuration: %d\n",form->configuration);
    printf("Hybrid: ");
    if (form->hybrid==1){
      printf("Yes\n");
    } else {
      printf("No\n");
    }
    printf("Antennae included: %d\n",nantsused);
    printf("Baselines: %d\n",nbl);
    printf("Central Frequency: %d MHz\n",form->frequency);
    /*   printf("Antenna Efficiency: %.1f \%\n",efficiency); */
    printf("Source & Imaging:\n");
    printf("Source Declination: %.3f degrees\n",form->dec);
    printf("Time on source: %.1f minutes\n",form->integration);
    printf("Weighting Scheme: %s \n",weight);
    printf("Weighting Factor: %.3f x Natural\n",rfac);
    printf("Field of View (primary beam FWHM): %.1f %s\n",pbfwhm,pb_units);
    printf("Synthesised Beam Size (FWHM): %.2f\" x %.2f\"\n",res1,res2);
    if (form->track_baseline!=form->max_baseline){
      printf("Best Synthesised Beam Size (FWHM): %.2f\" x %.2f\"\n",mres1,mres2);
    }
    if (form->specific_zoom==1){
      printf("Specific Zoom Synthesised Beam Size (FWHM): %.2f\" x %.2f\"\n",sres1,sres2);
    }
    printf("Continuum/Coarse Spectrum:\n");
    printf("Effective Bandwidth: %.0f MHz\n",bw);
    printf("# Channels: %d\n",nchan);
    printf("Channel Bandwidth: %.3f MHz\n",sb);
    printf("Spectral Bandwidth: %.3f km/s\n",vwidth);
    printf("Spectral Channel Resolution: %.3f km/s\n",vres);
    printf("Zoom Band:\n");
    printf("# Channels: 2048\n");
    printf("Channel Bandwidth: %.3f kHz\n",sbz*1000.0);
    printf("Spectral Channel Resolution: %.3f km/s\n",vres2);
    if (form->specific_zoom==1){
      printf("Specific Spectral Channel Resolution: %.3f km/s\n",vres2s);
    }
  } else {
    printf("<table style=\"border: 1px solid #000;\" >\n");
    printf("<tr><th style=\"color: red; text-align: right\">Configuration parameters:</th>\n");
    printf("<td><table><tr>\n");
    printf("<th>Configuration:</th><td>%d</td>\n",form->configuration);
    printf("<th>Hybrid</th>");
    if (form->hybrid==1){
      printf("<td>Yes</td>\n");
    } else {
      printf("<td>No</td>\n");
    }
    printf("<th>Antennae included:</th><td>%d</td>\n",nantsused);
    printf("<th>Baselines:</th><td>%d</td>\n",nbl);
    printf("</tr></table></td></tr>\n");
    printf("<tr><th></th><td><table><tr>\n");
    printf("<th>Central Frequency:</th><td>%d MHz</td>\n",form->frequency);
    printf("<th>Antenna Efficiency:</th><td>%.1f %%</td>\n",(efficiency*100.0));
    printf("</tr></table></td></tr>\n");
    printf("<tr><th style=\"color: red; text-align: right\">Source & Imaging:</th>\n");
    printf("<td><table><tr>\n");
    printf("<th>Source Declination:</th><td>%.3f degrees</td>\n",form->dec);
    printf("<th>Time on source:</th><td>%.1f minutes</td>\n",form->integration);
    printf("</tr></table></td></tr>\n");
    printf("<th></th><td><table><tr>\n");
    printf("<th>Weighting Scheme:</th><td>%s</td>\n",weight);
    printf("<th>Weighting Factor:</th><td>%.3f x Natural</td>\n",rfac);
    printf("</tr></table></td></tr>\n");
    printf("<th></th><td><table><tr>\n");
    printf("<th>Field of View (primary beam FWHM):</th><td>%.1f %s</td>\n",pbfwhm,pb_units);
    printf("<th>Synthesised Beam Size (FWHM):</th><td>%.2f\" x %.2f\"</td>\n",res1,res2);
    printf("</tr></table></td></tr>\n");
    if ((form->max_baseline!=form->track_baseline)||
	(form->specific_zoom==1)){
      printf("<th></th><td><table><tr>\n");
      if (form->max_baseline!=form->track_baseline){
	printf("<th>Best Synthesised Beam Size (FWHM):</th>");
	printf("<td>%.2f\" x %.2f\"",mres1,mres2);
	printf("<img src=\"/tooltip_icon.gif\" title=\"Best synthesised beam size is achieved "
	       "when CA06 is included in the array.\" \></td>\n");
      }
      if (form->specific_zoom==1){
	printf("<th>Specific Zoom Band Synthesised Beam Size (FWHM):</th>");
	printf("<td>%.2f\" x %.2f\"",sres1,sres2);
      }
      printf("</tr></table></td></tr>\n");
    }
    printf("<tr><th style=\"color: red; text-align: right\">Continuum/Coarse Spectrum:</th>\n");
    printf("<td><table><tr>\n");
    printf("<th>Effective Bandwidth:</th><td>%.0f MHz</td>\n",bw);
    printf("<th># Channels:</th><td>%d</td>\n",nchan);
    printf("<th>Channel Bandwidth:</th><td>%.3f MHz</td>\n",sb);
    printf("</tr></table></td></tr>\n");
    printf("<th></th><td><table><tr>\n");
    printf("<th>Spectral Bandwidth:</th><td>%.3f km/s</td>\n",vwidth);
    printf("<th>Spectral Channel Resolution:</th><td>%.3f km/s</td>\n",vres);
    printf("</tr></table></td></tr>\n");
    printf("<tr><th style=\"color: red; text-align: right\">Zoom Band:</th>\n");
    printf("<td><table><tr>\n");
    printf("<th># Channels:</th><td>2048</td>\n");
    printf("<th>Channel Bandwidth:</th><td>%.3f kHz</td>\n",sbz*1000.0);
    printf("<th>Spectral Channel Resolution:</th><td>%.3f km/s</td>\n",vres2);
    printf("</tr></table></td></tr>\n");
    if (form->specific_zoom==1){
      printf("<tr><th style=\"color: red; text-align: right\">Specific Zoom Band:</th>\n");
      printf("<td><table><tr>\n");
      printf("<th># Channels:</th><td>2048</td>\n");
      printf("<th>Channel Bandwidth:</th><td>%.3f kHz</td>\n",sbz*1000.0);
      printf("<th>Spectral Channel Resolution:</th><td>%.3f km/s</td>\n",vres2s);
      printf("</tr></table></td></tr>\n");
    }
    printf("</table><br />\n");
  }

  if (form->html_output==1){
    printf("<table class=\"sensresults\" style=\"text-align: center; border-collapse: collapse;border: 1px #6699CC solid;\">\n");
    printf("<tr><th rowspan=\"2\"></th><th colspan=\"%d\">Good Weather</th>\n",ncc);
    if ((twelvemm==1)||(sevenmm==1)||(threemm==1)){
      printf("<th colspan=\"%d\">Average Weather</th>\n",ncc);
      printf("<th colspan=\"%d\">Mediocre Weather</th>\n",ncc);
    }
    printf("</tr><tr>\n");
    for (i=0;i<calcn;i++){
      printf("<th>Continuum</th><th>Spectral</th><th>Zoom</th>");
      if (form->specific_zoom==1){
	printf("<th>S_Zoom</th>");
      }
      printf("\n");
    }
    printf("</tr>\n");
    printf("<tr><th style=\"text-align: right\">System Temperature (K)</th>\n");
    for (i=0;i<calcn;i++){
      printf("<td colspan=\"3\">%.1f</td>",tsys[i]);
      if (form->specific_zoom==1){
	printf("<td>%.1f</td>",sz_tsys[i]);
      }
      printf("\n");
    }
    printf("</tr>\n");
    printf("<tr><th style=\"text-align: right\">Antenna Sensitivity (Jy)</th>\n");
    for (i=0;i<calcn;i++){
      printf("<td colspan=\"%d\">%.0f</td>\n",ncc,ssen_single[i]);
    }
    printf("</tr>\n");
    printf("<tr><th style=\"text-align: right\">Array Sensitivity (Jy)</th>\n");
    for (i=0;i<calcn;i++){
      printf("<td colspan=\"%d\">%.0f</td>\n",ncc,ssen_all[i]);
    }
    printf("</tr>\n");
    printf("<tr><th style=\"text-align: right\">RMS Noise Level (mJy/beam)</th>\n");
    for (i=0;i<calcn;i++){
      printf("<td>%.3f</td><td>%.3f</td><td>%.3f</td>",
	     rms[i],sbrms[i],sbrmsz[i]);
      if (form->specific_zoom==1){
	printf("<td>%.3f</td>",sbrmszs[i]);
      }
    }
    printf("</tr>\n");
    printf("<tr><th style=\"text-align: right\">Brightness Temperature Sensitivity (K)</th>\n");
    for (i=0;i<calcn;i++){
      bt_format(bt[i],outformat[0]);
      bt_format(sbbt[i],outformat[1]);
      bt_format(sbbtz[i],outformat[2]);
      snprintf(tmpformat,BUFSIZE,"<td>%s</td><td>%s</td><td>%s</td>",
	       outformat[0],outformat[1],outformat[2]);
      printf(tmpformat,bt[i],sbbt[i],sbbtz[i]);
      bt_format(sbbtzs[i],outformat[0]);
      snprintf(tmpformat,BUFSIZE,"<td>%s</td>",outformat[0]);
      if (form->specific_zoom==1){
	printf(tmpformat,sbbtzs[i]);
      }
      printf("\n");
    }
    printf("</tr>\n");
    printf("</table>\n");

  } else {
    for (i=0;i<calcn;i++){
      printf("Sensitivity ");
      switch (i){
      case 0:
	printf("(Good weather)\n");
	break;
      case 1:
	printf("(Average weather)\n");
	break;
      case 2:
	printf("(Poor weather)\n");
	break;
      }
      printf("System Temperature: %.1f K\n",tsys[i]);
      printf("Antenna Sensitivity: %.0f Jy\n",ssen_single[i]);
      printf("Array Sensitivity: %.0f Jy\n",ssen_all[i]);
      printf("RMS noise level: %.3f (C) / %.3f (S) / %.3f (Z)",
	     rms[i],sbrms[i],sbrmsz[i]);
      if (form->specific_zoom==1){
	printf(" / %.3f (SZ)",sbrmszs[i]);
      }
      printf(" mJy/beam\n");
      printf("Brightness Temperature Sensitivity: %.3f (C) / %.3f (S) / %.3f (Z)",
	     bt[i],sbbt[i],sbbtz[i]);
      if (form->specific_zoom==1){
	printf(" / %.3f (SZ)",sbbtzs[i]);
      }
      printf(" K\n");
    }
  }
  
}

void bt_format(float bt,char *format){
  if (bt>1){
    strcpy(format,"%.1f");
  } else if (bt>0.1){
    strcpy(format,"%.2f");
  } else if (bt>0.01){
    strcpy(format,"%.3f");
  } else if (bt>0.001){
    strcpy(format,"%.4f");
  } else if (bt>0.0001){
    strcpy(format,"%.5f");
  } else if (bt>0.00001){
    strcpy(format,"%.6f");
  } else if (bt>0.000001){
    strcpy(format,"%.7f");
  }
}

void minmax(float *array,int n_array,float *min,float *max){
  int i;
  
  *min=array[0];
  *max=array[0];
  for (i=1;i<n_array;i++){
    if (array[i]<*min){
      *min=array[i];
    }
    if (array[i]>*max){
      *max=array[i];
    }
  }
}

float calculate_btsens(float rms,float wavesq,float res1,float res2){
  /* the brightness temperature sensitivity comes from AT technical document 
     AT/01.17/025, but has 1.36 instead of 1.46 (why? I don't know). Other than
     that, this equation doesn't actually have fudge factors :) */
  float bt;

  bt=1.36*rms*wavesq/(res1*res2);

  return (bt);
}

void calculate_systemsens(float dishdiameter,int nantsused,float tsys,
			  float efficiency,float *ssen_single,float *ssen_all){
  /* the system sensitivity equation comes from AT technical document AT/01.17/025,
     but has 3514 instead of 3.5 x 10^3 at the beginning of the equation. JS changed
     this equation to have the antenna diameter as the effective diameter of all
     antennae combined, instead of just one antenna. */
  float effective_diameter;

  effective_diameter=dishdiameter*sqrtf((float)nantsused); /* do the algebra, it reduces
							      to this */
  *ssen_single=3514*tsys/(efficiency*powf(dishdiameter,2));
  *ssen_all=3514*tsys/(efficiency*powf(effective_diameter,2));
  
}

float calculate_rms(float rfac,float tsys,float efficiency,float dishdiameter,
		    float effbw,float tint,int nbl,int polproductscombined){
  /* the RMS equation comes directly from AT technical document AT/01.17/025, and
     assumes that for CABB (an 8-bit correlator) that the correlator efficiency is
     1, and that Stokes I is being made (ie. data from both linear polarisations
     are being combined). */
  float rms;
  rms=300.0*tsys*rfac/(efficiency*powf(dishdiameter,2)*
		       sqrtf(effbw*tint*(float)nbl*(float)polproductscombined));
  return (rms);
}

void calculate_rms_array(float rfac,system_temperature *tsys,float efficiency,
			 float dishdiameter,float totalbw,float effbw,float tint,
			 int nbl,int polproductscombined,float centrefreq,
			 int *ants,int n_ants,float *otsys,float **rms_array,
			 float **freq_array,int *n_rms_array,float sz_freq,
			 float **sz_tsys){
  /* the RMS equation comes directly from AT technical document AT/01.17/025, and
     assumes that for CABB (an 8-bit correlator) that the correlator efficiency is
     1, and that Stokes I is being made (ie. data from both linear polarisations
     are being combined). */
  float low_freq,high_freq,chanfreq_low,chanfreq_high;
  float *rms=NULL,*rms_average=NULL,*rms_poor=NULL,sz_rms[3];
  float *systemps=NULL,*systemps_average=NULL,*systemps_poor=NULL;
  int nchans,i,j,k,*rms_n=NULL,sz_rms_n=0;

  low_freq=centrefreq-totalbw/2.0;
  high_freq=centrefreq+totalbw/2.0;
  nchans=totalbw/effbw;
  
  rms=calloc(nchans,sizeof(float));
  rms_average=calloc(nchans,sizeof(float));
  rms_poor=calloc(nchans,sizeof(float));
  rms_n=calloc(nchans,sizeof(int));
  sz_rms[0]=sz_rms[1]=sz_rms[2]=0;

  for (i=0;i<n_ants;i++){
    for (j=0;j<nchans;j++){
      chanfreq_low=low_freq+(float)j*effbw;
      chanfreq_high=low_freq+(float)(j+1)*effbw;
      for (k=0;k<tsys->chan_nchans[ants[i]];k++){
	if ((tsys->chan_freqs[ants[i]][k]>=chanfreq_low)&&
	    (tsys->chan_freqs[ants[i]][k]<chanfreq_high)){
	  rms[j]+=tsys->chan_tsys[ants[i]][k];
	  rms_average[j]+=tsys->chan_tsys_average[ants[i]][k];
	  rms_poor[j]+=tsys->chan_tsys_poor[ants[i]][k];
	  rms_n[j]++;
	  if ((sz_freq>=chanfreq_low)&&
	      (sz_freq<chanfreq_high)){
	    sz_rms[0]+=tsys->chan_tsys[ants[i]][k];
	    sz_rms[1]+=tsys->chan_tsys_average[ants[i]][k];
	    sz_rms[2]+=tsys->chan_tsys_poor[ants[i]][k];
	    sz_rms_n++;
	  }
	}
      }
    }
  }
  *n_rms_array=0;
  *rms_array=NULL;
  *freq_array=NULL;
  for (i=0;i<nchans;i++){
    if ((rms_n[i]>0)&&
	(rms[i]>0)){
      rms[i]/=rms_n[i];
      rms_average[i]/=rms_n[i];
      rms_poor[i]/=rms_n[i];
      (*n_rms_array)++;
      *rms_array=realloc(*rms_array,*n_rms_array*sizeof(float));
      *freq_array=realloc(*freq_array,*n_rms_array*sizeof(float));
      (*rms_array)[*n_rms_array-1]=300.0*rms[i]*rfac/(efficiency*powf(dishdiameter,2)*
						     sqrtf(effbw*tint*(float)nbl*
							   (float)polproductscombined));
      (*freq_array)[*n_rms_array-1]=low_freq+(float)i*effbw;
      systemps=realloc(systemps,*n_rms_array*sizeof(float));
      systemps_average=realloc(systemps_average,*n_rms_array*sizeof(float));
      systemps_poor=realloc(systemps_poor,*n_rms_array*sizeof(float));
      systemps[*n_rms_array-1]=rms[i];
      systemps_average[*n_rms_array-1]=rms_average[i];
      systemps_poor[*n_rms_array-1]=rms_poor[i];
    }
  }
  if ((sz_rms_n>0)&&(sz_rms>0)){
    for (i=0;i<3;i++){
      sz_rms[i]/=sz_rms_n;
      (*sz_tsys)[i]=sz_rms[i];
    }
  }

  otsys[0]=calc_average(systemps,*n_rms_array);
  otsys[1]=calc_average(systemps_average,*n_rms_array);
  otsys[2]=calc_average(systemps_poor,*n_rms_array);

}

float calc_average(float *array,int n_array){
  int i;
  float sum=0;

  for (i=0;i<n_array;i++){
    sum+=array[i];
  }

  sum/=n_array;

  return (sum);
}

void read_file(char *file,float bandwidth,float chanwidth,int nchans,
	       float centrefreq,form *form,int *ants,int n_ants,system_temperature *tsys){
  int i,j,k,file_nlines=0;
  FILE *fp=NULL;
  float *file_freq=NULL,*file_tsys=NULL,tmp_freq,tmp_tsys;
  float tau[3],tr;
  char line_input[BUFSIZE];

  /* initialise the structure, and allocate the required space */
  if (tsys->chan_freqs==NULL){
    tsys->chan_freqs=malloc((MAX_NANTS+1)*sizeof(float*));
    tsys->chan_n=malloc((MAX_NANTS+1)*sizeof(int*));
    tsys->chan_tsys=malloc((MAX_NANTS+1)*sizeof(float*));
    tsys->chan_tsys_average=malloc((MAX_NANTS+1)*sizeof(float*));
    tsys->chan_tsys_poor=malloc((MAX_NANTS+1)*sizeof(float*));
    tsys->chan_nchans=malloc((MAX_NANTS+1)*sizeof(int));
    for (i=0;i<=MAX_NANTS;i++){
      (tsys->chan_freqs)[i]=malloc(nchans*sizeof(float));
      (tsys->chan_n)[i]=malloc(nchans*sizeof(int));
      (tsys->chan_tsys)[i]=malloc(nchans*sizeof(float));
      (tsys->chan_tsys_average)[i]=malloc(nchans*sizeof(float));
      (tsys->chan_tsys_poor)[i]=malloc(nchans*sizeof(float));
    }
  }

  for (i=0;i<nchans;i++){
    (tsys->chan_freqs)[0][i]=centrefreq+(float)(i-(nchans/2))*chanwidth;
    (tsys->chan_n)[0][i]=0;
    (tsys->chan_tsys)[0][i]=0.0;
    (tsys->chan_tsys_average)[0][i]=0.0;
    (tsys->chan_tsys_poor)[0][i]=0.0;
  }

  /* read the file if we have one */
  if (strlen(file)>0){
    if (form->html_output==0){
      printf("- reading file %s\n",file);
    }
    fp=fopen(file,"r");
    while(fgets(line_input,BUFSIZE,fp)!=NULL){
      if (sscanf(line_input,"%f %f",&tmp_freq,&tmp_tsys)==2){
	file_nlines++;
	file_freq=realloc(file_freq,file_nlines*sizeof(float));
	file_tsys=realloc(file_tsys,file_nlines*sizeof(float));
	file_freq[file_nlines-1]=tmp_freq*1000.0;
	file_tsys[file_nlines-1]=powf(10,tmp_tsys);
      }
    }
    fclose(fp);

    for (i=0;i<nchans;i++){
      for (j=0;j<file_nlines;j++){
	if ((file_freq[j]>=(tsys->chan_freqs[0][i]-chanwidth/2))&&
	    (file_freq[j]<(tsys->chan_freqs[0][i]+chanwidth/2))){
	  if (form->do_atm==1){
	    for (k=0;k<3;k++){
	      tau[k]=interp(form->asize,form->tau[k],form->fr,
			    tsys->chan_freqs[0][i]);
	    }
	    tsys->chan_tsys[0][i]+=form->mfactor*calc_tsys(form->halimit,form->ellimit,
							  form->dec,file_tsys[j],tau[0]);
	    tsys->chan_tsys_average[0][i]+=form->mfactor*calc_tsys(form->halimit,form->ellimit,
								  form->dec,file_tsys[j],tau[1]);
	    tsys->chan_tsys_poor[0][i]+=form->mfactor*calc_tsys(form->halimit,form->ellimit,
							       form->dec,file_tsys[j],tau[2]);
	  } else {
	    tsys->chan_tsys[0][i]+=file_tsys[j];
	    tsys->chan_tsys_average[0][i]+=file_tsys[j];
	    tsys->chan_tsys_poor[0][i]+=file_tsys[j];
	  }
	  tsys->chan_n[0][i]++;
	}
      }
      if (tsys->chan_n[0][i]>0){
	tsys->chan_tsys[0][i]/=tsys->chan_n[0][i];
	tsys->chan_tsys_average[0][i]/=tsys->chan_n[0][i];
	tsys->chan_tsys_poor[0][i]/=tsys->chan_n[0][i];
      }
	
    }

  } else {
    for (i=0;i<nchans;i++){
      if (form->do_atm==1){
	tr=interp(form->asize,form->tr,form->fr,tsys->chan_freqs[0][i]);
	for (k=0;k<3;k++){
	  tau[k]=interp(form->asize,form->tau[k],form->fr,
			tsys->chan_freqs[0][i]);
	}
	tsys->chan_tsys[0][i]=form->mfactor*calc_tsys(form->halimit,form->ellimit,
						      form->dec,tr,tau[0]);
	tsys->chan_tsys_average[0][i]=form->mfactor*calc_tsys(form->halimit,form->ellimit,
							      form->dec,tr,tau[1]);
	tsys->chan_tsys_poor[0][i]=form->mfactor*calc_tsys(form->halimit,form->ellimit,
							   form->dec,tr,tau[2]);
      }
    }
  }	

  for (i=0;i<n_ants;i++){
    tsys->chan_nchans[ants[i]]=nchans;
    for (j=0;j<nchans;j++){
      tsys->chan_freqs[ants[i]][j]=tsys->chan_freqs[0][j];
      tsys->chan_n[ants[i]][j]=tsys->chan_n[0][j];
      tsys->chan_tsys[ants[i]][j]=tsys->chan_tsys[0][j];
      tsys->chan_tsys_average[ants[i]][j]=tsys->chan_tsys_average[0][j];
      tsys->chan_tsys_poor[ants[i]][j]=tsys->chan_tsys_poor[0][j];
    }
  }

}

float calc_tsys(float halim,float ellim,float dec,float trec,float tau){
  /* some ATCA parameters */
  /* t0 is the temperature of the atmosphere. According to equation 13.120 of TM&S
     this is about 13-20K below the ambient temperature on the ground, hence we'll set
     it at 270K.
     ellim is the elevation limit of the ATCA, but we use 30 degrees here as it is
     recommended that mm observations don't go below this level (the atmosphere becomes a
     big problem at low elevations). */
  
  float t0=270.0,lat=-30.31288472,pi=3.141592654;
  float cosl,sinl,sinel,sind,cosd,ha,h,tsys,nat,uni;
  float cosha_at_ellimit,ha_at_ellimit,hah_at_ellimit,cosha;
  int n=100,i;

  cosl=cosf(pi/180.0*lat);
  sinl=sinf(pi/180.0*lat);
  sinel=sinf(pi/180.0*ellim);
  sind=sinf(pi/180.0*dec);
  cosd=cosf(pi/180.0*dec);

  /* determine the HA limits */
  
  /* determine what the hour angle would be at the elevation limit
     check out the equations on http://home.att.net/~srschmitt/script_celestial2horizon.html
     to figure out what is going on here */
  cosha_at_ellimit=sinel/(cosd*cosl)-(sind*sinl)/(cosd*cosl);
  if (fabsf(cosha_at_ellimit)<=1){
    ha_at_ellimit=acosf(cosha_at_ellimit)*180.0/pi; /* this is in degrees */
    hah_at_ellimit=ha_at_ellimit/15.0; /* this is in hours */
    if (hah_at_ellimit>halim){
      /* use the specified hour angle limit rather than the elevation limit */
      ha=halim;
    } else {
      /* use the elevation limit rather than the specified hour angle limit */
      ha=hah_at_ellimit;
    }
  } else {
    /* the source doesn't go below the elevation limit, so just use
       the preset HA limit */
    ha=halim;
  }

  nat=0.0;
  uni=0.0;
  ha*=pi/12.0;
  for (i=0;i<n;i++){
    h=ha*(float)i/(float)n;
    cosha=cosf(h);
    sinel=sinl*sind+cosl*cosd*cosha;
    /* tsys seems to come from equation 13.119 of Thompson, Moran and Swenson
       note that sin(el) = cos(90-el); TM&S ask for sec(z) which is the same as
       1/sin(el). The 2.7 is the CMB temperature */
    tsys=trec+t0*(1-expf(-1*tau/sinel))+2.7*expf(-1*tau/sinel);
    uni+=tsys;
    nat+=1/(tsys*tsys);
  }
  uni/=n;
  nat/=n;
  nat=1/sqrtf(nat);

  return (0.5*(uni+nat));
}

void tsys_structure(float bandwidth,float channelwidth,float centrefreq,
		    form *form,system_temperature *tsys){
  int nchans=(int)(bandwidth/channelwidth);
  int ants_all[6]={1,2,3,4,5,6};
  int ants_new_l[2]={2,3};
  int ants_old_l[4]={1,4,5,6};

  if ((centrefreq>=TWENTYCM_FREQ_LOW-300)&&
      (centrefreq<=TWENTYCM_FREQ_HIGH)){
    /* L band */
    read_file("systemps/ca02_21cm_x_polarisation.avg",bandwidth,channelwidth,nchans,
	      centrefreq,form,ants_all,6,tsys);
/*     read_file("systemps/ca01_21cm_x_polarisation.avg",bandwidth,channelwidth,nchans, */
/* 	      centrefreq,form,ants_old_l,4,tsys); */
  } else if ((centrefreq>=THIRTEENCM_FREQ_LOW)&&
	     (centrefreq<=THIRTEENCM_FREQ_HIGH)){
    /* S band */
    read_file("systemps/ca02_21cm_x_polarisation.avg",bandwidth,channelwidth,nchans,
	      centrefreq,form,ants_all,6,tsys);
/*     read_file("systemps/ca01_13cm_x_polarisation.avg",bandwidth,channelwidth,nchans, */
/* 	      centrefreq,form,ants_old_l,4,tsys); */
  } else if ((centrefreq>=SIXCM_FREQ_LOW)&&
	     (centrefreq<=SIXCM_FREQ_HIGH)){
    /* C band */
    read_file("systemps/ca04_6cm_x_polarisation_run1.avg",bandwidth,channelwidth,nchans,
	      centrefreq,form,ants_all,6,tsys);
  } else if ((centrefreq>=THREECM_FREQ_LOW)&&
	     (centrefreq<=THREECM_FREQ_HIGH)){
    /* X band */
    read_file("systemps/ca03_3cm_x_polarisation_run1.avg",bandwidth,channelwidth,nchans,
	      centrefreq,form,ants_all,6,tsys);
  } else if ((centrefreq>=TWELVEMM_FREQ_LOW)&&
	     (centrefreq<=TWELVEMM_FREQ_HIGH)){
    /* K band */
    read_file("systemps/12mm_recvtemps.avg",bandwidth,channelwidth,nchans,centrefreq,
	      form,ants_all,6,tsys);
  } else if ((centrefreq>=SEVENMM_FREQ_LOW)&&
	     (centrefreq<=SEVENMM_FREQ_HIGH)){
    /* Q band */
    read_file("systemps/ca02_7mm.avg",bandwidth,channelwidth,nchans,centrefreq,
	      form,ants_all,6,tsys);
  } else {
    /* this band has no CABB-derived system temperature measurements */
    read_file("",bandwidth,channelwidth,nchans,centrefreq,form,ants_all,6,tsys);
  }
}

void assign_weight(float *rfac,float *bfac,int configuration,
		   float *r_array,float *b_array,int *config_array,int array_size){
  int i;
  
  for (i=0;i<array_size;i++){
    if (config_array[i]==configuration){
      *rfac=r_array[i];
      *bfac=b_array[i];
      break;
    }
  }
}
    

float interp(int size,float *t,float *f,float freq){
  float t0,t1,t2,f1,f2,m,c;
  int y;

  for (y=0;y<(size-1);y++){
    if ((f[y]<freq)&&(f[y+1]>freq)){
      t1=t[y];
      t2=t[y+1];
      f1=f[y];
      f2=f[y+1];
      m=(t2-t1)/(f2-f1);
      c=t2-m*f2;
      t0=m*freq+c;
    } else if (f[y]==freq){
      t0=t[y];
    }
  }
  return (t0);
}
