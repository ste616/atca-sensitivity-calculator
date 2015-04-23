#!/usr/bin/perl

use strict;
use Math::Trig;
use CGI qw(:standard);
use CGI::Carp qw(warningsToBrowser fatalsToBrowser);

# ATCA sensitivity calculator.
# History:
#  3-Apr-2001	Steven Tingay	Original version
# 20-May-2003   Bob Sault	Added 12mm capability
# 14-Sep-2003   Bob Sault	Tidy up. Handle hybrid arrays.
#  8-Jan-2004   Bob Sault       Better estimates of Tsys for 12mm system.
# 14-Jan-2004   Bob Sault       Simple handling of 3mm system.
#  2-Feb-2004   Bob Sault       Bug fix to freq=1216 MHz.
# 31-May-2004   Bob Sault       Give bandwidth info.
#  3-Aug-2004   Bob Sault	Update 12mm data (care of Ravi).
# 31-Oct-2005   Bob Sault       Updated 3mm sys temperatures.
#                               Included elevation dependence of Tsys
#                               and 3 weather conditions.
# 12-Jun-2007   Phil Edwards    Added 7mm.
#                               Included the same 3 weather conditions
#                               with opacities kindly provided by Bob.  
# 14-Nov-2008   Phil Edwards    Add first approximation of CABB
# 13-Nov-2009   Phil Edwards    Add second approximation of CABB with zooms
#  3-Dec-2009   Jamie Stevens   Make equations more transparent, attribute their
#                               sources and make them more accurate. Still more
#                               improvements should be made in cleaning up this
#                               calculator.
#  4-Dec-2009   Jamie Stevens   Major recode and cleanup. Most calculations into
#                               subroutines, creates all webpages, change web
#                               appearance, add extra options for calculations.
#  6-Jul-2010   Jamie Stevens   Use CABB system temperature measurements for those
#                               receivers that have been measured, and calculate
#                               sensitivity on a per-channel basis.

# Bugs:
#  - The resolution in the DEC direction for hybrid arrays is
#    very simplistic.
#  - No account is made of shadowing in the compact configurations,
#    or of the source being below the elevation limit.

#### main program loop begins

# get the inputs to the form before we make the webpage so we can
# keep the inputs as the user selected them
my %form;

$form{"parameters_present"}=0;
foreach my $p (param()){
    $form{$p}=param($p);
    $form{"parameters_present"}=1;
}

# start creating the web page
%form=&create_static_web_page(%form);

# create the results part of the web page
if ($form{"parameters_present"}==1){
    &present_results(%form);
}

# print the usage information at the bottom of the page
&print_usage_information;

print end_html;

#### main program loop ends

#### subroutines begin here

# create_static_web_page makes the web page with the form and information
# for its usage
sub create_static_web_page {
    # get our arguments
    my (%form)=@_;

    # start making the web page
    print header;
    print start_html(-title => "ATCA CABB Sensitivity Calculator",
		     -style => { -src => '/stylesheets/ca_style.css'},
		     -style => { -src => '/stylesheets/senscalc_style.css'});
    
    # put the top titlebar on and the menu underneath it
    print<<EOD;
    <!-- BEGIN HEADER -->
	
	<table width="100%" bgcolor="#159bcb" border="0" cellpadding="0" cellspacing="0">
	<tr>
	<td bgcolor="#FFFFFF" width="70"><a href="http://www.csiro.au/"><img border=0 src="/images/csiro50spaced.gif" alt="CSIRO logo"></a></td>
	<td> <table background="/images/csiro50backgr.gif" width="100%" height="70" bgcolor="#ffffff" border="0" cellpadding="0" cellspacing="0">
        <tr>
	<td align="left" valign="bottom" style="color: white; padding: 10px">
	<span style="font-size: 200%">CABB Sensitivity Calculator<br /></span>
	<span style="font-size: 150%">Australia Telescope Compact Array</span><br /></td>
	<td align="right"><img src="/images/green50.gif" alt="Green End Bar" /></td>

        </tr>
      </table></td>
    </tr>

    <tr>
      <td bgcolor="#FFFFFF"><img src="/images/spacer.gif" alt="Spacer image"></td>
      <td><div class="navbar" align="left">
        <a href="http://www.atnf.csiro.au/">ATNF Home</a>&nbsp;&nbsp;
        <a href="/">Narrabri Home</a>&nbsp;&nbsp;

        <a href="/astronomy/astro_info.html">Monitoring</a>&nbsp;&nbsp;
        <a href="/observing/observing.html">Observing</a>&nbsp;&nbsp;
        <a href="/computing/">Computing</a>&nbsp;&nbsp;
        <a href="/staff/ATCA_contact.html">Contact</a>&nbsp;&nbsp;
        <a href="/sitemap/sitemap.html">Site Map</a>&nbsp;&nbsp;
        <a href="/feedback/">Feedback</a>&nbsp;&nbsp;

      </div></td>
    </tr>
  </table>
  <!-- END HEADER -->
EOD


  # we'll use divs instead of frames
  # first is the div on the left that will present the configuration
  # options to the user
  print "<div style=\"position: relative;\">";
  print "<div style=\"float: left; width: 300px; border-colour: #000000; border-width: 0;".
    " border-style: solid; background: #ffffff\">\n";
  
  print h2("Inputs");
#  print "configuration=".$form{"configuration"}."\n";
    
  print startform;
    
    # the array configuration dropbox
    my @configuration_values=("6000","3000","1500","750","367","h214",
			      "h168","h75");
    my @configuration_labels=("6km","3km","1.5km","750m","EW352/367","H214",
			      "H168","H75");
    print "<table style=\"width: 100%\">\n";
    print "<tr>";
    print "<th align=\"right\">Configuration:</th>";
    print "<td align=\"left\"><select name=\"configuration\">";
    for (my $i=0;$i<=$#configuration_values;$i++){
	print "<option value=\"".$configuration_values[$i]."\"";
	if (($form{"parameters_present"}==1)&&
	    ($form{"configuration"} eq $configuration_values[$i])){
	    print " selected=\"selected\"";
	}
	print ">".$configuration_labels[$i]."</option>";
    }
    print "</select></td></tr>\n";
    
    # the central frequency
    print "<tr>";
    print "<th align=\"right\">Centre Frequency (MHz):</th>";
    if ($form{"parameters_present"}==0){
	$form{"frequency"}="5500";
    }
    print "<td align=\"left\"><input type=\"text\" name=\"frequency\" value=\"".$form{"frequency"}.
	"\" size=\"6\" maxlength=\"6\"/>";
    print "</td></tr>\n";
    
    # the CABB correlator configuration
    my @bandwidth_values=("CFB1M","CFB4M","CFB16M","CFB64M");
    my @bandwidth_labels=("CFB 1M-0.5k","CFB 4M-2k","CFB 16M-8k","CFB 64M-32k");
    print "<tr>";
    print "<th align=\"right\">Observing Bandwidth:</th>";
    print "<td align=\"left\"><select name=\"bandwidth\">";
    for (my $i=0;$i<=$#bandwidth_values;$i++){
	print "<option value=\"".$bandwidth_values[$i]."\"";
	if (($form{"parameters_present"}==1)&&
	    ($form{"bandwidth"} eq $bandwidth_values[$i])){
	    print " selected=\"selected\"";
	}
	print ">".$bandwidth_labels[$i]."</option>";
    }
    print "</select></td></tr>\n";

    # the image weighting scheme
    my @weight_values=("N","R2","R1","R0","R-1","R-2","U","SU");
    my @weight_labels=("Natural","Robust=2","Robust=1","Robust=0","Robust=-1",
		       "Robust=-2","Uniform","Superuniform");
    print "<tr>";
    print "<th align=\"right\">Image weighting scheme:</th>";
    print "<td align=\"left\"><select name=\"weight\">";
    for (my $i=0;$i<=$#weight_values;$i++){
	print "<option value=\"".$weight_values[$i]."\"";
	if (($form{"parameters_present"}==1)&&
	    ($form{"weight"} eq $weight_values[$i])){
	    print " selected=\"selected\"";
	    $form{"weight_selected"}=$weight_labels[$i];
	}
	print ">".$weight_labels[$i]."</option>";
    }
    print "</select></td></tr>\n";

    # source declination
    print "<tr>";
    print "<th align=\"right\">Source declination (deg):</th>";
    if ($form{"parameters_present"}==0){
	$form{"dec"}="-30";
    }
    print "<td align=\"left\"><input type=\"text\" name=\"dec\" value=\"".$form{"dec"}.
	"\" size=\"8\" />";
    print "</td></tr>\n";

    # integration time
    print "<tr>";
    print "<th align=\"right\">Integration time (min):</th>";
    if ($form{"parameters_present"}==0){
	$form{"integration"}="720";
    }
    print "<td align=\"left\"><input type=\"text\" name=\"integration\" value=\"".
	$form{"integration"}."\" size=\"5\" />";
    print "</td></tr>\n";

    # elevation limit
    print "<tr>";
    print "<th align=\"right\">Elevation limit:</th>";
    if ($form{"parameters_present"}==0){
	$form{"ellimit"}="12";
    }
    print "<td align=\"left\"><input type=\"text\" name=\"ellimit\" value=\"".$form{"ellimit"}.
	"\" size=\"2\" maxlen=\"2\" />";
    print "</td></tr>\n";

    # hour angle limit
    print "<tr>";
    print "<th align=\"right\">Hour-angle limit:</th>";
    if ($form{"parameters_present"}==0){
	$form{"halimit"}="6";
    }
    print "<td align=\"left\"><input type=\"text\" name=\"halimit\" value=\"".$form{"halimit"}.
	"\" size=\"2\" maxlen=\"2\" />";
    print "</td></tr>\n";

    # use antenna 6?
    print "<tr>";
    print "<th align=\"right\">Use CA06?:</th>";
    if ($form{"parameters_present"}==0){
	$form{"useca06"}="yes";
    }
    print "<td align=\"left\"><input type=\"checkbox\" name=\"useca06\" value=\"yes\"";
    if ($form{"useca06"} eq "yes"){
	print " checked=\"checked\"";
    }
    print " />";
    print "</td></tr>\n";
    
    print "</table>\n";

    # the submit button
#    print "<input type=\"submit\" value=\"CALCULATE\">\n";
    print submit(-name=>'CALCULATE');

    print endform;
    
    print "</div>\n";

    return %form;
}

sub print_usage_information {

    # put the information section at the bottom of the web page
    print "</div>\n";
    print "<div style=\"width:98%; position: relative; clear: both; top: 20px;\">\n";
    print "<hr noshade /><br />\n";

    print h2("Usage Information");
    print "This page provides a means of estimating the characteristics of ATCA observations with the";
    print " <a href=\"http://www.narrabri.atnf.csiro.au/observing/CABB.html\" target=\"_blank\">";
    print "Compact Array Broadband Backend</a> (CABB) system. The calculator allows both available";
    print " and planned CABB modes to be selected: please check the";
    print " <a href=\"http://www.narrabri.atnf.csiro.au/observing/CABB.html\" target=\"_blank\">";
    print "CABB webpage</a> for the modes that have been implemented.<br /><br />\n";
    print "The <a href=\"http://www.atnf.csiro.au/observers/docs/at_sens/index_old.html\" target=\"_blank\">";
    print "pre-CABB sensitivity calculator</a> is still available and may be useful for those";
    print " considering archival ATCA data.<br /><br />\n";
    print "The calculator includes the theoretical RMS noise in a resultant image (Stokes I, Q, U, or V).";
    print " The corresponding brightness temperature sensitivity is also calculated.  These estimates are based";
    print " on the expressions appearing in the ATNF technical document";
    print " <a href=\"http://www.narrabri.atnf.csiro.au/observing/AT-01.17-025.pdf\" target=\"_blank\">";
    print "AT/01.17/025</a>, the calculations of antenna efficiency as a function of frequency,";
    print " revised (CABB era) measurements of system temperature as a function of frequency,";
    print " and simulations of the effects of different weighting schemes on images made with different ATCA";
    print " configurations. In calculating the effects of weighting, 30 second samples and";
    print " <em>MIRIAD</em> default cell and image sizes were assumed.";
    print " For CABB  it is assumed that the full 2GHz is available at 4GHz and above, and that";
    print " 500MHz is available at 20cm and 13cm. RFI may reduce the usable bandwidth,";
    print " particularly at 20cm.<br /><br />\n";
    print "It is assumed that the nominated integration time is evenly spread over a 12 hour observation.";
    print " Note the time given is the integration time: this does not account for overheads";
    print " involved in calibration. Depending on the calibration scheme used, these overheads might vary between 5% for simple";
    print " 20cm observations, to 50% for 3mm observations.<br /><br />\n";

    print "Page last updated: 4-Dec-2009.<br />\n";
    print "This tool was originally developed by Steven Tingay and Lister Staveley-Smith, and developed further by Bob Sault, Phil Edwards and Jamie Stevens.<br /><br />\n";

    print "</div>\n";

}

sub read_file {
    my ($tsys_ref,$file,$bandwidth,$chanwidth,$nchans,$centrefreq,@ants)=@_;

    my %tsys=%{$tsys_ref};

    my @chan_freqs;
    my @chan_n;
    my @chan_tsys;
    for (my $i=0;$i<$nchans;$i++){
	$chan_freqs[$i]=$centrefreq+($i-($nchans/2))*$chanwidth;
	$chan_n[$i]=0;
	$chan_tsys[$i]=0;
    }
    if ($file ne ""){
	open(FILE,$file);
	my @file_freq;
	my @file_tsys;
	while(<FILE>){
	    chomp;
	    my $line=$_;
	    $line=~s/^\s*//;
	    my @els=split(/\s+/,$line);
	    push @file_freq,$els[0];
	    push @file_tsys,$els[1];
	}
	close(FILE);

	for (my $i=0;$i<=$#chan_freqs;$i++){
	    for (my $j=0;$j<=$#file_freq;$j++){
		if (($file_freq[$j]>=($chan_freqs[$i]-$chanwidth/2))&&
		    ($file_freq[$j]<($chan_freqs[$i]+$chanwidth/2))){
		    $chan_tsys[$i]+=$file_tsys[$j];
		    $chan_n[$i]++;
		}
	    }
	    if ($chan_n[$i]>0){
		$chan_tsys[$i]/=$chan_n[$i];
	    }
	}
    } else {
	for (my $i=0;$i<=$#chan_freqs;$i++){
	    $chan_tsys[$i]=$bandwidth;
	}
    }

    for (my $i=0;$i<=$#ants;$i++){
	@{$tsys{"channels_ca0$ants[$i]"}}=@chan_freqs;
	@{$tsys{"tsys_ca0$ants[$i]"}}=@chan_tsys;
    }
}

sub present_results {
    my (%form)=@_;

    # begin by making a div to the right of the Inputs div
    print "<div style=\"float: left;\">";
    print h2("Results");

    # get some systemp files

    # this next bit is the parameters we need to do the calculations
    # a list of frequencies, in MHz, that we have data for. You will note
    # that the CABB recommended cm frequencies are NOT here yet!
    my @naf=(1200, 1500, 1800, 2100, 2300, 2500, 4400, 5900, 7400, 8800,10600,
	     16000,16500,17000,17500,18000,18500,19000,19500,20000,20500,21000,
	     21500,22000,22500,23000,23500,24000,24500,25000,25400,
	     30000,31000,32000,33000,34000,35000,36000,37000,38000,39000,
	     40000,41000,42000,43000,44000,45000,46000,47000,48000,49000,50000,
	     83781.1, 85556.2, 86834.3, 88680.5, 90526.6, 91946.7, 94005.9,
	     95852.1, 97272.2, 98976.3,100254.4,102200.0,102300.0,106432.0);
    
    # a list of antenna efficiencies for each frequency in @naf
    my @na= (0.66, 0.69, 0.62, 0.52, 0.51, 0.53, 0.65, 0.72, 0.65, 0.64, 0.65, 
	     0.58, 0.62, 0.63, 0.65, 0.67, 0.70, 0.68, 0.64, 0.64, 0.60, 0.53,
	     0.55, 0.54, 0.51, 0.51, 0.53, 0.49, 0.49, 0.46, 0.47,
	     0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60,
	     0.60, 0.59, 0.58, 0.57, 0.56, 0.55, 0.54, 0.53, 0.52, 0.51, 0.50,
	     0.3297,0.3065,0.3020,0.2856,0.2689,0.2670,0.2734,
	     0.2727,0.2521,0.2403,0.2336,0.2322,0.14,0.14);
    
    # arrays beginning with 'w' relate to the 3mm band
    my @wtr=   (280.0, 255.0, 220.0, 178.0, 143.0, 140.0,     
		150.0, 155.0, 163.0, 182.0, 192.0);
    my @wf=    (83857, 85785, 87571, 89714, 91857, 95071,
		97285, 99071,101214,102928,104785);
    my @wtau1= (0.140,0.136,0.134,0.133,0.134,0.137,
		0.140,0.145,0.150,0.157,0.166);      
    my @wtau2= (0.173,0.171,0.171,0.172,0.174,0.180,
		0.185,0.191,0.199,0.208,0.219);      
    my @wtau3= (0.220,0.221,0.222,0.226,0.231,0.240,
		0.248,0.257,0.267,0.279,0.293);      
    
    # arrays beginning with 'q' relate to the 7mm band
    my @qtr = ( 40.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 
		32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0);
    my @qf=   (30000,31000,32000,33000,34000,35000,36000,37000,38000,39000,
	       40000,41000,42000,43000,44000,45000,46000,47000,48000,49000,50000);
    my @qtau1=(0.040,0.041,0.042,0.044,0.047,0.050,0.053,0.057,0.062,0.067,
	       0.073,0.081,0.089,0.100,0.113,0.129,0.148,0.174,0.208,0.255,0.325);
    my @qtau2=(0.048,0.048,0.050,0.052,0.054,0.057,0.061,0.065,0.070,0.075,
	       0.082,0.089,0.099,0.110,0.123,0.139,0.160,0.186,0.221,0.270,0.342);
    my @qtau3=(0.059,0.059,0.060,0.062,0.065,0.068,0.071,0.076,0.081,0.087,
	       0.094,0.101,0.112,0.123,0.136,0.153,0.174,0.201,0.237,0.286,0.359,);
    
    # arrays beginning with 'k' relate to the 12mm band
    my @ktr = ( 30.0, 25.9, 23.2, 22.0, 21.2, 21.4, 22.4, 22.9, 23.6, 22.6, 20.3,
		19.4, 19.9, 19.2, 19.1, 18.6, 17.8, 20.1, 22.7, 28.3);
    my @kf=   (16000,16500,17000,17500,18000,18500,19000,19500,20000,20500,21000,
	       21500,22000,22500,23000,23500,24000,24500,25000,25400);
    my @ktau1=(0.017,0.018,0.019,0.021,0.023,0.026,0.030,0.034,0.040,0.047,0.056,
	       0.064,0.072,0.075,0.073,0.068,0.062,0.057,0.053,0.049);
    my @ktau2=(0.019,0.021,0.023,0.025,0.029,0.033,0.037,0.044,0.052,0.062,0.074,
	       0.087,0.097,0.101,0.098,0.091,0.083,0.075,0.068,0.063);
    my @ktau3=(0.023,0.025,0.028,0.032,0.036,0.041,0.048,0.057,0.069,0.083,0.101,
	       0.119,0.133,0.139,0.134,0.124,0.111,0.100,0.090,0.082);
    
    # arrays beginning with 'x' relate to the 3cm band
    my @xt=(45.35,42.78,43.24,40.71,37.86,38.70,39.68,41.22,42.03,43.06);
    my @xf=(8000,8128,8256,8384,8512,8640,8768,8896,9024,9152);
    
    # arrays beginning with 'c' relate to the 6cm band
    my @ct=(90.94,46.96,37.57,34.05,33.35,32.79,32.29,33.57,33.90,33.26,32.85,32.58,31.28,31.22,33.82,35.53,43.34,49.72,73.28,119.47);
    my @cf=(4288,4416,4544,4672,4800,4928,5056,5184,5312,5440,5568,5696,5824,5952,6080,6208,6336,6464,6592,6720);

    # arrays beginning with 's' relate to the 13cm band
    my @st=(38.35,37.09,34.15,33.71,35.70,41.58,63.34);
    my @sf=(2240,2304,2368,2432,2496,2560,2624);
    
    # arrays beginning with 'l' relate to the 21cm band
    my @lt=(47.48,39.70,32.60,31.81,29.64,33.14,30.71,29.00,31.78);
    my @lf=(1216,1280,1344,1408,1472,1536,1600,1664,1751);
    
    my %RN= (75,1,122,1,168,1,214,1,367,1,375,1,750,1,1500,1,3000,1,6000,1);
    my %RR2=(75,1,122,1,168,1,214,1,367,1,375,1,750,1,1500,1,3000,1,6000,1);
    my %RR1=(75,1,122,1,168,1,214,1,367,1,375,1,750,1,1500,1.01,3000,1.01,6000,1.01);
    
    my %BN=(75,0.77,122,0.95,168,0.75,214,0.74,367,1.09,375,0.97,750,0.96,1500,0.96,3000,0.97,6000,1.32);
    my %BR2=(75,0.77,122,0.95,168,0.75,214,0.74,367,1.09,375,0.97,750,0.96,1500,0.96,3000,0.97,6000,1.32);

    my (%RR0,%RR_1,%RR_2,%RU,%RSU,%BR1,%BR0,%BR_1,%BR_2,%BU,%BSU);
    if ($form{"configuration"} =~ /h/) {
#	$halim = 4;
	$form{"hybrid"} = 1;
	%RR0=(75,1.37,122,1.33,168,1.34,214,1.18,367, 1.22,375,1.25,750,1.21,1500,1.18,3000,1.16,6000,1.16);
	%RR_1=(75,1.63,122,1.82,168,2.22,214,1.52,367,1.63,375,1.74,750,1.42,1500,1.33,3000,1.23,6000,1.22);
	%RR_2=(75,1.63,122,1.84,168,2.31,214,1.54,367,1.65,375,1.76,750,1.43,1500,1.33,3000,1.24,6000,1.22);
	%RU=(75,1.63,122,1.84,168,2.32,214,1.54,367,1.65,375,1.77,750,1.43,1500,1.33,3000,1.24,6000,1.22);
	%RSU=(75,3.43,122,4.00,168,1.85,214,1.65,367,1.80,375,1.77,750,1.54,1500,1.44,3000,1.33,6000,1.32);
	%BR1=(75,0.76,122,0.91,168,0.74,214,0.73,367,1.00,375,0.90,750,0.88,1500,0.88,3000,0.89,6000,1.32);
	%BR0=(75,0.58,122,0.61,168,0.61,214,0.64,367,0.68,375,0.62,750,0.62,1500,0.64,3000,0.66,6000,0.84);
	%BR_1=(75,0.53,122,0.55,168,0.59,214,0.62,367,0.64,375,0.58,750,0.59,1500,0.62,3000,0.64,6000,0.80);
	%BR_2=(75,0.53,122,0.55,168,0.59,214,0.62,367,0.64,375,0.58,750,0.59,1500,0.62,3000,0.64,6000,0.80);
	%BU=(75,0.53,122,0.55,168,0.59,214,0.62,367,0.64,375,0.58,750,0.59,1500,0.62,3000,0.64,6000,0.80);
	%BSU=(75,0.52,122,0.54,168,0.59,214,0.59,367,0.61,375,0.59,750,0.60,1500,0.61,3000,0.63,6000,0.76);
    } else {
#	$halim = 6;
	$form{"hybrid"} = 0;
	%RR0=(75,1.37,122,1.33,168,1.34,214,1.17,367, 1.22,375,1.25,750,1.21,1500,1.18,3000,1.16,6000,1.16);
	%RR_1=(75,1.63,122,1.82,168,2.22,214,1.33,367,1.63,375,1.74,750,1.42,1500,1.33,3000,1.23,6000,1.22);
	%RR_2=(75,1.63,122,1.84,168,2.31,214,1.33,367,1.65,375,1.76,750,1.43,1500,1.33,3000,1.24,6000,1.22);
	%RU=(75,1.63,122,1.84,168,2.32,214,1.33,367,1.65,375,1.77,750,1.43,1500,1.33,3000,1.24,6000,1.22);
	%RSU=(75,3.43,122,4.00,168,1.85,214,1.78,367,1.80,375,1.77,750,1.54,1500,1.44,3000,1.33,6000,1.32);
	%BR1=(75,0.76,122,0.91,168,0.74,214,0.91,367,1.00,375,0.90,750,0.88,1500,0.88,3000,0.89,6000,1.32);
	%BR0=(75,0.58,122,0.61,168,0.61,214,0.69,367,0.68,375,0.62,750,0.62,1500,0.64,3000,0.66,6000,0.84);
	%BR_1=(75,0.53,122,0.55,168,0.59,214,0.67,367,0.64,375,0.58,750,0.59,1500,0.62,3000,0.64,6000,0.80);
	%BR_2=(75,0.53,122,0.55,168,0.59,214,0.67,367,0.64,375,0.58,750,0.59,1500,0.62,3000,0.64,6000,0.80);
	%BU=(75,0.53,122,0.55,168,0.59,214,0.67,367,0.64,375,0.58,750,0.59,1500,0.62,3000,0.64,6000,0.80);
	%BSU=(75,0.52,122,0.54,168,0.59,214,0.62,367,0.61,375,0.59,750,0.60,1500,0.61,3000,0.63,6000,0.76);
    }

    # now do the calculations!
    $form{"configuration"}=~s/h//;
    $form{"configuration"}=~s/ew//;

    # Compute the antenna beam efficiency.
    
    my $efficiency = interp(int(@naf),@na,@naf,$form{"frequency"});

    # Determine the system temperature. The "interp" routine returns
    # the system temperature in variable $tsys.

    my $twelvemm = 0; my $sevenmm = 0; my $threemm = 0;
    my ($tr,$tau,$tsys1,$tsys2,$tsys3);
    if ($form{"frequency"}>=83857 && $form{"frequency"}<=104785) {
	$tr    = interp(int(@wf),@wtr,  @wf,$form{"frequency"});
	$tau   = interp(int(@wf),@wtau1,@wf,$form{"frequency"});
	$tsys1 = 2.3 * calc_tsys($form{"halimit"},$form{"ellimit"},$form{"dec"},$tr,$tau);
	$tau   = interp(int(@wf),@wtau2,@wf,$form{"frequency"});
	$tsys2 = 2.3 * calc_tsys($form{"halimit"},$form{"ellimit"},$form{"dec"},$tr,$tau);
	$tau   = interp(int(@wf),@wtau3,@wf,$form{"frequency"});
	$tsys3 = 2.3 * calc_tsys($form{"halimit"},$form{"ellimit"},$form{"dec"},$tr,$tau);
	$threemm = 1;
    } elsif ($form{"frequency"}>=30000 && $form{"frequency"}<=50000){
	$tr    = interp(int(@qf),@qtr,  @qf,$form{"frequency"});
	$tau   = interp(int(@qf),@qtau1,@qf,$form{"frequency"});
	$tsys1 = 2 * calc_tsys($form{"halimit"},$form{"ellimit"},$form{"dec"},$tr,$tau);
	$tau   = interp(int(@qf),@qtau2,@qf,$form{"frequency"});
	$tsys2 = 2 * calc_tsys($form{"halimit"},$form{"ellimit"},$form{"dec"},$tr,$tau);
	$tau   = interp(int(@qf),@qtau3,@qf,$form{"frequency"});
	$tsys3 = 2 * calc_tsys($form{"halimit"},$form{"ellimit"},$form{"dec"},$tr,$tau);
	$sevenmm = 1;
    } elsif ($form{"frequency"}>=16000 && $form{"frequency"}<=25000) {
	$tr    = interp(int(@kf),@ktr,  @kf,$form{"frequency"});
	$tau   = interp(int(@kf),@ktau1,@kf,$form{"frequency"});
	$tsys1 = 1.4 * calc_tsys($form{"halimit"},$form{"ellimit"},$form{"dec"},$tr,$tau);
	$tau   = interp(int(@kf),@ktau2,@kf,$form{"frequency"});
	$tsys2 = 1.4 * calc_tsys($form{"halimit"},$form{"ellimit"},$form{"dec"},$tr,$tau);
	$tau   = interp(int(@kf),@ktau3,@kf,$form{"frequency"});
	$tsys3 = 1.4 * calc_tsys($form{"halimit"},$form{"ellimit"},$form{"dec"},$tr,$tau);
	$twelvemm = 1;
    }elsif ($form{"frequency"}>=8000 && $form{"frequency"}<=9499) {
	$tsys1 = 1.8 * interp(int(@xf),@xt,@xf,$form{"frequency"});
    }elsif ($form{"frequency"}>=4288 && $form{"frequency"}<=6720) {
	$tsys1 = 2.3 * interp(int(@cf),@ct,@cf,$form{"frequency"});
    }elsif ($form{"frequency"}>=2000 && $form{"frequency"}<=2999) {
	$tsys1 = 2.5 * interp(int(@sf),@st,@sf,$form{"frequency"});
    }elsif ($form{"frequency"}>=1730 && $form{"frequency"}<=1999) {
	$tsys1 = 2 * interp(int(@lf),@lt,@lf,$form{"frequency"});
    }else {
	print "<b>The frequency you have selected is out of the valid range, please try again.<br />Valid ranges are: 1730 to 1999 MHz; 2000 to 2999 MHz; 4288 to 6720 MHz; 8000 to 9499 MHz; 16000 to 25000 MHz; 30000 to 50000 MHz; and 83870 to 104780 MHz.</b><br />";
	return;
    } 

    # Determine the number of baselines to use
    if ($threemm){
	$form{"useca06"}="";
    }
    my ($nbl,$nantsused);
    if (($form{"configuration"}==6000 && $form{"useca06"} eq "yes")
	|| $form{"useca06"} eq "yes"){
	$nbl=15;
	$nantsused=6;
    } else {
	$nbl=10;
	$nantsused=5;
    }

    # do some error checking
    if (($form{"dec"}==0 && !$form{"hybrid"})||
	($form{"dec"}<-90) || ($form{"dec"}>90) || ($form{"integration"}<=0)){
	print "<b>Please choose declinations greater than -90&#176; (other than zero), and non-zero integration times.</b><br />";	
	return;
    }
    if ($form{"ellimit"}<12 || $form{"ellimit"}>90 ||
	$form{"halimit"}<=0 || $form{"halimit"}>12){
	print "<b>Please choose an elevation limit between 12 and 90 degrees, and a positive, non-zero hour-angle limit less than 12 hours.</b><br />";
    }
    
    my $obw=$form{"bandwidth"};
    my ($bw,$sb,$nchan);
    if($form{"bandwidth"} eq "CFB1M"){
        $obw="CFB1M-0.5k";
        if($form{"frequency"}>4000){
          $bw=2048; $sb=1; $nchan=2048; 
        }else {
          $bw=500;  $sb=1;  $nchan=500;
        }
    }

    if($form{"bandwidth"} eq "CFB4M"){
        $obw="CFB4M-2k";
        if($form{"frequency"}>4000){
          $bw=2048; $sb=4; $nchan=512; 
        }else {
          $bw=500;  $sb=4;  $nchan=128;
        }
    }

    if($form{"bandwidth"} eq "CFB16M"){
        $obw="CFB16M-8k";
        if($form{"frequency"}>4000){
          $bw=2048; $sb=16; $nchan=128; 
        }else {
          $bw=500;  $sb=16;  $nchan=32;
        }
    }

    if($form{"bandwidth"} eq "CFB64M"){
        $obw="CFB64M-32k";
        if($form{"frequency"}>4000){
          $bw=2048; $sb=64; $nchan=32; 
        }else {
          $bw=500;  $sb=64;  $nchan=8;
        }
    }

    my $sbz=$sb/2048.;

    my $effbw=$bw;
    my ($weight,$rfac,$bfac);
    if($form{"weight"} eq "N"){
	$weight="Natural";
	$rfac=$RN{$form{"configuration"}};
	$bfac=$BN{$form{"configuration"}};
    }elsif($form{"weight"} eq "R2"){
	$weight="Robust=2";
	$rfac=$RR2{$form{"configuration"}};
	$bfac=$BR2{$form{"configuration"}};
    }elsif ($form{"weight"} eq "R1") {
	$weight="Robust=1";
	$rfac=$RR1{$form{"configuration"}};
	$bfac=$BR1{$form{"configuration"}};
    }elsif ($form{"weight"} eq "R0") {
	$weight="Robust=0";
	$rfac=$RR0{$form{"configuration"}};
	$bfac=$BR0{$form{"configuration"}};
    }elsif ($form{"weight"} eq "R-1") {
	$weight="Robust=-1";
	$rfac=$RR_1{$form{"configuration"}};
	$bfac=$BR_1{$form{"configuration"}};
    }elsif ($form{"weight"} eq "R-2") {
	$weight="Robust=-2";
	$rfac=$RR_2{$form{"configuration"}};
	$bfac=$BR_2{$form{"configuration"}};
    }elsif ($form{"weight"} eq "U") {
	$weight="Uniform";
	$rfac=$RU{$form{"configuration"}};
	$bfac=$BU{$form{"configuration"}};
    }elsif ($form{"weight"} eq "SU") {
	$weight="Superuniform";
	$rfac=$RSU{$form{"configuration"}};
	$bfac=$BSU{$form{"configuration"}};
    }

    # $efficiency           Antenna efficiency
    # $form{"integration"}  Integration time, in minutes.
    # $nbl                  Number of baselines.
    # $tsys                 System temperature, in K.
    # $rfac                 RMS factor: Amount it exceeds natural weighting rms by.
    # $bfac                 Some sort of beam size fudge factor.
    # $nchan                Number of channels.
    # $bw	            Total bandwidth, in MHz.
    # $form{"frequency"}    Observing frequency, in MHz.
    # $effbw                Effective continuum bandwidth, in MHz.
    # $sb	            Effective spectral channel bandwidth.
    # $sbz	            Effective zoom spectral channel bandwidth.
    
    # $rms	            Continuum sensitivity, in mJy/beam.
    # $ssen	            System sensitivity, in Jy.
    # $res1	            Beam size in RA direction, in arcsec.
    # $res2	            Beam size in DEC direction, in arcsec.
    # $bt	            Brightness temperature sensitivity, in K.
    # $sbrms                Spectral band sensitivity, in mJy/beam
    # $sbbt	            Spectral band brightness temperature sensitivity, in K.
    # $vres                 Spectral channel width (km/s).
    # $vwidth               Spectral bandwidth (km/s).
    # $pbfwhm               Primary beam FWHM.

    # some constants that we need
    my $dishdiameter=22; # dish diameter in m
    my $speedoflight=299792458; # speed of light in m/s
    my $radianstodegrees=180.0/pi; # conversion between radians and degrees
    my $degreestoarcmin=60.0; # conversion between degrees and arcminutes
    my $metrestokilometres=1.0/1000.0; # conversion between metres and kilometres
    my $mhztohz=1e6; # conversion between MHz and Hz
    my $metrestocentimetres=100.0; # conversion between metres and cm
    my $degreestoarcsec=3600.0; # conversion between degrees and arcseconds

    # and some simple derived quantities
    my $pbfwhm = ($speedoflight/$dishdiameter)/($form{"frequency"}*$mhztohz) * $radianstodegrees*$degreestoarcmin;
    my $vres =   ($speedoflight*$metrestokilometres)*$sb/$form{"frequency"};
    my $vres2 =  ($speedoflight*$metrestokilometres)*$sbz/$form{"frequency"};
    my $vwidth = ($speedoflight*$metrestokilometres)*$bw/$form{"frequency"};
    my $wavesq=(($speedoflight*$metrestocentimetres/$mhztohz)/$form{"frequency"})**2; # in cm**2

    # work out the synthesised beam size
    my $res1=$bfac*$speedoflight/(($form{"frequency"}*$mhztohz)*$form{"configuration"})*
	$radianstodegrees*$degreestoarcsec;
    my $res2;
    if($form{"hybrid"}){
	$res2 = $res1;
    }else{
	$res2=$res1/abs(sin($form{"dec"}/$radianstodegrees));  
    }

    # the number of polarisation products we combine to get the final output
    # we choose 2 here, which is XX & YY -> Stokes I
    my $polproductscombined=2;
    my %system_temperatures=&tsys_hash($effbw,$sb,$form{"frequency"},$tsys1);
    my @usable_antenna=(1,2,3,4,5);
    if ($nantsused==6){
	push @usable_antenna,6;
    }
    # get the continuum RMS noise level for all weather (cm wavelengths), or
    # good weather (mm wavelengths)
    my @rms_array;
    ($tsys1,@rms_array)=&calculate_rms_array($rfac,\%system_temperatures,$efficiency,$dishdiameter,$effbw,$sb,
					     $form{"integration"},$nbl,$polproductscombined,$form{"frequency"},@usable_antenna);
    
#    my $rms1=&calculate_rms($rfac,$tsys1,$efficiency,$dishdiameter,$effbw,
#			    $form{"integration"},$nbl,$polproductscombined);
    my $rms1=&calc_average(@rms_array);

    # get the system sensitivity for each antenna and for all antennae combined
    my ($ssen_single1,$ssen_all1)=
	&calculate_systemsens($dishdiameter,$nantsused,$tsys1,$efficiency);

    # get the brightness temperature sensitivity
    my $bt1=&calculate_btsens($rms1,$wavesq,$res1,$res2);

    my ($sbrms1,$sbbt1,$sbrmsz1,$sbbtz1);
#    my (@sbrms1,@sbrmsz1);
    if ($nchan>1){
	# calculate the spectral line RMS noise level for all weather
	# (cm wavelengths) or good weather (mm wavelengths)
	$sbrms1=&calculate_rms($rfac,$tsys1,$efficiency,$dishdiameter,$sb,
			       $form{"integration"},$nbl,$polproductscombined);
#	@sbrms1=&calculate_rms_array($rfac,%system_temperatures,$efficiency,$dishdiameters,$effbw,$sb,
#				     $form{"integration"},$nbl,$polproductscombined,$form{"frequency"},@usable_antenna);
	$sbbt1=&calculate_btsens($sbrms1,$wavesq,$res1,$res2);
	$sbrmsz1=&calculate_rms($rfac,$tsys1,$efficiency,$dishdiameter,$sbz,
				$form{"integration"},$nbl,$polproductscombined);
#	@sbrmsz1=&calculate_rms_array($rfac,%system_temperatures,$efficiency,$dishdiameters,$effbw,$sbz,
#				      $form{"integration"},$nbl,$polproductscombined,$form{"frequency"},@usable_antenna);
	$sbbtz1=&calculate_btsens($sbrmsz1,$wavesq,$res1,$res2);
    }

    my ($rms2,$ssen_single2,$ssen_all2,$bt2,$sbrms2,$sbbt2,$sbrmsz2,$sbbtz2);
    my ($rms3,$ssen_single3,$ssen_all3,$bt3,$sbrms3,$sbbt3,$sbrmsz3,$sbbtz3);
    
    if ($twelvemm || $sevenmm || $threemm){
	# do the same stuff for average weather
	$rms2=&calculate_rms($rfac,$tsys2,$efficiency,$dishdiameter,$effbw,
			     $form{"integration"},$nbl,$polproductscombined);
	($ssen_single2,$ssen_all2)=
	    &calculate_systemsens($dishdiameter,$nantsused,$tsys2,$efficiency);
	$bt2=&calculate_btsens($rms2,$wavesq,$res1,$res2);
	# do the same stuff for mediocre weather
	$rms3=&calculate_rms($rfac,$tsys3,$efficiency,$dishdiameter,$effbw,
			     $form{"integration"},$nbl,$polproductscombined);
	($ssen_single3,$ssen_all3)=
	    &calculate_systemsens($dishdiameter,$nantsused,$tsys3,$efficiency);
	$bt3=&calculate_btsens($rms3,$wavesq,$res1,$res2);
	if ($nchan>1){
	    # average weather
	    $sbrms2=&calculate_rms($rfac,$tsys2,$efficiency,$dishdiameter,$sb,
				   $form{"integration"},$nbl,$polproductscombined);
	    $sbbt2=&calculate_btsens($sbrms2,$wavesq,$res1,$res2);
	    $sbrmsz2=&calculate_rms($rfac,$tsys2,$efficiency,$dishdiameter,$sbz,
				    $form{"integration"},$nbl,$polproductscombined);
	    $sbbtz2=&calculate_btsens($sbrmsz2,$wavesq,$res1,$res2);
	    # mediocre weather
	    $sbrms3=&calculate_rms($rfac,$tsys3,$efficiency,$dishdiameter,$sb,
				   $form{"integration"},$nbl,$polproductscombined);
	    $sbbt3=&calculate_btsens($sbrms3,$wavesq,$res1,$res2);
	    $sbrmsz3=&calculate_rms($rfac,$tsys3,$efficiency,$dishdiameter,$sbz,
				    $form{"integration"},$nbl,$polproductscombined);
	    $sbbtz3=&calculate_btsens($sbrmsz3,$wavesq,$res1,$res2);
	}
    }

    # print out the results to the webpage
    # first, round long numbers to only the necessary number of significant figures
    $sbz = int(1000000*$sbz)/1000;
    $vres = int(1000*$vres)/1000;
    $vres2 = int(1000*$vres2)/1000;
    $vwidth = int(1000*$vwidth)/1000;
    if($pbfwhm > 2){
	$pbfwhm = int(10*$pbfwhm+0.5)/10;
        $pbfwhm = "$pbfwhm arcmin";
    }else{
        $pbfwhm = int(60*$pbfwhm+0.5);
        $pbfwhm = "$pbfwhm arcsec";
    }
    $efficiency = int($efficiency*1000+0.5)/10;
    $res1 = int(100*$res1+0.5) / 100;
    $res2 = int(100*$res2+0.5) / 100;
    if($nchan > 1){
	$sb=int($sb*1000+0.5)/1000;
    }
    
    $rms1  = int(1000*$rms1+0.5)/1000;
    $ssen_single1 = int($ssen_single1);
    $ssen_all1 = int($ssen_all1);
    $tsys1 = int($tsys1*10+0.5)/10;
    
    $bt1 = btround($bt1);
    if ($nchan>1) {
	$sbrms1=int(100*$sbrms1+0.5)/100;
        $sbbt1 = sbbtround($sbbt1);
	$sbrmsz1=int(100*$sbrmsz1+0.5)/100;
        $sbbtz1 = sbbtround($sbbtz1);
    }

    if($threemm||$sevenmm||$twelvemm){
        $rms2  = int(1000*$rms2+0.5)/1000;
        $rms3  = int(1000*$rms3+0.5)/1000;
        $ssen_single2 = int($ssen_single2);
	$ssen_all2 = int($ssen_all2);
        $ssen_single3 = int($ssen_single3);
	$ssen_all3 = int($ssen_all3);
        $tsys2 = int($tsys2*10+0.5)/10;
        $tsys3 = int($tsys3*10+0.5)/10;
        $bt2 = btround($bt2);
        $bt3 = btround($bt3);
        if ($nchan>1) {
	    $sbrms2=int(100*$sbrms2+0.5)/100;
	    $sbrms3=int(100*$sbrms3+0.5)/100;
	    $sbbt2 = sbbtround($sbbt2);
	    $sbbt3 = sbbtround($sbbt3);
	    $sbrmsz2=int(100*$sbrmsz2+0.5)/100;
	    $sbbtz2 = sbbtround($sbbtz2);
	    $sbrmsz3=int(100*$sbrmsz3+0.5)/100;
	    $sbbtz3 = sbbtround($sbbtz3);
        }
    }
    
    print "<table style=\"border: 1px solid #000;\" >";
    print "<tr><th style=\"color: red; text-align: right\">Configuration parameters:</th>";
    print "<td><table><tr>";
    print "<th>Configuration:</th><td>".$form{"configuration"}."</td>";
    print "<th>Hybrid:</th>";
    if ($form{"hybrid"}){
	print "<td>Yes</td>";
    } else {
	print "<td>No</td>";
    }
    print "<th>Antennae included:</th><td>".$nantsused."</td>";
    print "<th>Baselines:</th><td>".$nbl."</td>\n";
    print "</tr></table></td></tr>";
    print "<tr><th></th><td><table>";
    print "<th>Central Frequency:</th><td>".$form{"frequency"}." MHz</td>";
    print "<th>Antenna Efficiency:</th><td>".$efficiency."%</td>";
    print "</tr></table></td></tr>";
    print "<tr><th style=\"color: red; text-align: right\">Source & Imaging:</th>";
    print "<td><table><tr>";
    print "<th>Source Declination:</th><td>".$form{"dec"}." degrees</td>";
    print "<th>Time on source:</th><td>".$form{"integration"}." minutes</td>";
    print "</tr></table></td></tr>";
    print "<th></th><td><table><tr>";
    print "<th>Weighting Scheme:</th><td>".$form{"weight_selected"}."</td>";
    print "<th>Weighting Factor:</th><td>".$rfac." x Natural</td>";
    print "</tr></table></td></tr>";
    print "<th></th><td><table><tr>";
    print "<th>Field of View (primary beam FWHM):</th><td>".$pbfwhm."</td>";
    print "<th>Synthesised Beam Size (FWHM):</th><td>".$res1."\" x ".$res2."\"</td>";
    print "</tr></table></td></tr>";
    print "<tr><th style=\"color: red; text-align: right\">Continuum/Coarse Spectrum:</th>";
    print "<td><table><tr>";
    print "<th>Effective Bandwidth:</th><td>".$effbw." MHz</td>";
    print "<th># Channels:</th><td>".$nchan."</td>";
    print "<th>Channel Bandwidth:</th><td>".$sb." MHz</td>";
    print "</tr></table></td></tr>";
    print "<th></th><td><table><tr>";
    print "<th>Spectral Bandwidth:</th><td>".$vwidth." km/s</td>";
    print "<th>Spectral Channel Resolution:</th><td>".$vres." km/s</td>";
    print "</tr></table></td></tr>";
    print "<tr><th style=\"color: red; text-align: right\">Zoom Band:</th>";
    print "<td><table><tr>";
    print "<th># Channels:</th><td>2048</td>";
    print "<th>Channel Bandwidth:</th><td>".$sbz." kHz</td>";
    print "<th>Spectral Channel Resolution:</th><td>".$vres2." km/s</td>";
    print "</tr></table></td></tr>";
    print "</table>\n";
    print "<br />";
    print "<table class=\"sensresults\" style=\"text-align: center; border-collapse: collapse;border: 1px #6699CC solid;\">";
    print "<tr><th rowspan=\"2\"></th><th colspan=\"3\">Good Weather</th>";
    print "<th colspan=\"3\">Average Weather</th>";
    print "<th colspan=\"3\">Mediocre Weather</th></tr>";
    print "<tr><th>Continuum</th><th>Spectral</th><th>Zoom</th>";
    print "<th>Continuum</th><th>Spectral</th><th>Zoom</th>";
    print "<th>Continuum</th><th>Spectral</th><th>Zoom</th></tr>";
    print "<tr><th style=\"text-align: right\">System Temperature (K)</th>";
    print "<td colspan=\"3\">".$tsys1."</td>";
    if ($threemm || $sevenmm || $twelvemm){
	print "<td colspan=\"3\">".$tsys2."</td>";
	print "<td colspan=\"3\">".$tsys3."</td>";
    } else {
	print "<td colspan=\"3\">N/A</td>";
	print "<td colspan=\"3\">N/A</td>";
    }
    print "</tr>";
    print "<tr><th style=\"text-align: right\">Antenna Sensitivity (Jy)</th>";
    print "<td colspan=\"3\">".$ssen_single1."</td>";
    if ($threemm || $sevenmm || $twelvemm){
	print "<td colspan=\"3\">".$ssen_single2."</td>";
	print "<td colspan=\"3\">".$ssen_single3."</td>";
    } else {
	print "<td colspan=\"3\">N/A</td>";
	print "<td colspan=\"3\">N/A</td>";
    }
    print "</tr>";
    print "<tr><th style=\"text-align: right\">Array Sensitivity (Jy)</th>";
    print "<td colspan=\"3\">".$ssen_all1."</td>";
    if ($threemm || $sevenmm || $twelvemm){
	print "<td colspan=\"3\">".$ssen_all2."</td>";
	print "<td colspan=\"3\">".$ssen_all3."</td>";
    } else {
	print "<td colspan=\"3\">N/A</td>";
	print "<td colspan=\"3\">N/A</td>";
    }
    print "</tr>";
    print "<tr><th style=\"text-align: right\">RMS noise level (mJy/beam)</th>";
    print "<td>".$rms1."</td>";
    print "<td>".$sbrms1."</td>";
    print "<td>".$sbrmsz1."</td>";
    if ($threemm || $sevenmm || $twelvemm){
	print "<td>".$rms2."</td>";
	print "<td>".$sbrms2."</td>";
	print "<td>".$sbrmsz2."</td>";
	print "<td>".$rms3."</td>";
	print "<td>".$sbrms3."</td>";
	print "<td>".$sbrmsz3."</td>";
    } else {
	print "<td colspan=\"3\">N/A</td>";
	print "<td colspan=\"3\">N/A</td>";
    }
    print "</tr>";
    print "<tr><th style=\"text-align: right\">Brightness Temperature Sensitivity (K)</th>";
    print "<td>".$bt1."</td>";
    print "<td>".$sbbt1."</td>";
    print "<td>".$sbbtz1."</td>";
    if ($threemm || $sevenmm || $twelvemm){
	print "<td>".$bt2."</td>";
	print "<td>".$sbbt2."</td>";
	print "<td>".$sbbtz2."</td>";
	print "<td>".$bt3."</td>";
	print "<td>".$sbbt3."</td>";
	print "<td>".$sbbtz3."</td>";
    } else {
	print "<td colspan=\"3\">N/A</td>";
	print "<td colspan=\"3\">N/A</td>";
    }
    print "</tr>";
    print "</table>\n";
    print "</div>\n";

}

sub sbbtround{
  my($sbbt) = @_;
  if ($sbbt > 1) {
    $sbbt=int(10*$sbbt+0.5)/10;
  }elsif ($sbbt < 1 && $sbbt > 0.1) {
    $sbbt=int($sbbt*10+0.5)/10;
  }elsif ($sbbt < 0.1 && $sbbt > 0.01) {
    $sbbt=int($sbbt*100+0.5)/100;
  }elsif ($sbbt < 0.01 && $sbbt > 0.001) {
    $sbbt=int($sbbt*1000+0.5)/1000;
  }elsif ($sbbt < 0.001 && $sbbt > 0.0001) {
    $sbbt=int($sbbt*10000+0.5)/10000;
  }elsif ($sbbt < 0.0001 && $sbbt > 0.00001) {
    $sbbt=int($sbbt*100000+0.5)/100000;
  }elsif ($sbbt < 0.00001 && $sbbt > 0.000001) {
    $sbbt=int($sbbt*1000000+0.5)/1000000;
  }
  return $sbbt;
}
#------------------------------------------------------------------------
# Round the brightness temperature.

sub btround{
  my($bt) = @_;
  if ($bt > 1) {
    $bt=int(10*$bt+0.5)/10;
  }elsif ($bt < 1 && $bt > 0.1) {
    $bt=int($bt*100+0.5)/100;
  }elsif ($bt < 0.1 && $bt > 0.01) {
    $bt=int($bt*100+0.5)/100;
  }elsif ($bt < 0.01 && $bt > 0.001) {
    $bt=int($bt*1000+0.5)/1000;
  }elsif ($bt < 0.001 && $bt > 0.0001) {
    $bt=int($bt*10000+0.5)/10000;
  }elsif ($bt < 0.0001 && $bt > 0.00001) {
    $bt=int($bt*100000+0.5)/100000;
  }elsif ($bt < 0.00001 && $bt > 0.000001) {
    $bt=int($bt*1000000+0.5)/1000000;
  }
  return $bt;
}
#------------------------------------------------------------------------
# Interpolate a value.

sub interp {
  my($size)=@_[0];
  my(@t)=@_[1..$size];
  my(@f)=@_[$size+1..2*$size];
  my($freq)=@_[2*$size+1];
  my($t0);

  $size=$size-1;
  for (my $y=0;$y<=$size;$y++) {
    if($f[$y]<$freq && $f[$y+1]>$freq){
      my $t1=$t[$y];
      my $t2=$t[$y+1];
      my $f1=$f[$y];
      my $f2=$f[$y+1];
      my $m=($t2-$t1)/($f2-$f1);
      my $c=$t2-$m*$f2;
      $t0=$m*$freq+$c;
    }elsif($f[$y]==$freq) {
      $t0=$t[$y];
    }
  }
  return $t0;
}

#------------------------------------------------------------------------
# return a hash of system temperatures, one for each channel of each
# antenna
sub tsys_hash {
    my ($bandwidth,$channelwidth,$centrefreq,$tsys)=@_;
    # bandwidth is the total bandwidth of the observation in MHz
    # channelwidth is the width of each channel in MHz
    # centrefreq is the frequency of the central channel in MHz
    # tsys is the system temperature in K to assume for each channel
    #  (for frequency configurations where the system temperatures are
    #   not known as precisely)

    # do we load a file?
    my $l_new_systemps_file="systemps/ca02_21cm_x_polarisation.avg";
    my $l_old_systemps_file="systemps/ca01_21cm_x_polarisation.avg";
    my $s_old_systemps_file="systemps/ca01_13cm_x_polarisation.avg";
    my $c_systemps_file="systemps/ca04_6cm_x_polarisation_run1.avg";
    my $x_systemps_file="systemps/ca03_3cm_x_polarisation_run1.avg";

    my %system_temperatures;
    my $nchans=int($bandwidth/$channelwidth);

    if (($centrefreq>=1000)&&($centrefreq<2000)){
	# L band
	&read_file(\%system_temperatures,$l_new_systemps_file,
		   $bandwidth,$channelwidth,$nchans,$centrefreq,2,3);
	&read_file(\%system_temperatures,$l_old_systemps_file,
		   $bandwidth,$channelwidth,$nchans,$centrefreq,1,4,5,6);
    } elsif (($centrefreq>=2000)&&($centrefreq<3000)){
	# S band
	&read_file(\%system_temperatures,$l_new_systemps_file,
		   $bandwidth,$channelwidth,$nchans,$centrefreq,2,3);
	&read_file(\%system_temperatures,$s_old_systemps_file,
		   $bandwidth,$channelwidth,$nchans,$centrefreq,1,4,5,6);
    } elsif (($centrefreq>=4000)&&($centrefreq<7000)){
	# C band
	&read_file(\%system_temperatures,$c_systemps_file,
		   $bandwidth,$channelwidth,$nchans,$centrefreq,1,2,3,4,5,6);
    } elsif (($centrefreq>=7000)&&($centrefreq<10000)){
	# X band
	&read_file(\%system_temperatures,$x_systemps_file,
		   $bandwidth,$channelwidth,$nchans,$centrefreq,1,2,3,4,5,6);
    } else {
	# currently everything else has no CABB-derived system temperature
	# measurements
	&read_file(\%system_temperatures,"",
		   $tsys,$channelwidth,$nchans,$centrefreq,1,2,3,4,5,6);
    }

    return %system_temperatures;
}

#------------------------------------------------------------------------
# Calculate Tsys, taking an average atmosphere.

sub calc_tsys{
  my($halim,$ellim,$dec,$trec,$tau) = @_;
  # t0 is the temperature of the atmosphere. According to equation 13.120 of TM&S
  # this is about 13-20K below the ambient temperature on the ground, hence we'll set
  # it at 270K.
  # ellim is the elevation limit of the ATCA, but we use 30 degrees here as it is
  # recommended that mm observations don't go below this level (the atmosphere becomes a
  # big problem at low elevations).
  my($t0,$lat,$n) = (270,-30.31288472,100);
  my($cosl,$sinl,$sinel,$sind,$cosd,$ha,$h,$tsys,$nat,$uni);

  $cosl = cos(pi/180*$lat);
  $sinl = sin(pi/180*$lat);
  $sinel = sin(pi/180*$ellim);
  $sind = sin(pi/180*$dec);
  $cosd = cos(pi/180*$dec);

# Determine the HA limits.

  # determine what the hour angle would be at the elevation limit
  # check out the equations on http://home.att.net/~srschmitt/script_celestial2horizon.html
  # to figure out what is going on here
  my $cosha_at_ellimit=$sinel/($cosd*$cosl)-($sind*$sinl)/($cosd*$cosl);
  my $ha_at_ellimit=acos($cosha_at_ellimit)*180.0/pi; # this is in degrees
  my $hah_at_ellimit=$ha_at_ellimit/15.0; # this is in hours
  if ($hah_at_ellimit>$halim){
      # use the specified hour angle limit rather than the elevation limit
      $ha=$halim;
  } else {
      # use the elevation limit rather than the specified hour angle limit
      $ha=$hah_at_ellimit;
  }

#  if(abs($sinel-$sinl*$sind) > abs($cosl*$cosd)){
#    $ha = $halim;
#  }else{
#    $t1 = ($sinel - $sinl*$sind ) / ( $cosl*$cosd );
#    $t2 = sqrt(1-$t1*$t1);
##    $ha = 12/$PI * atan2($t2,$t1);
#    $ha=12/$PI*($t2-$t1);
#    if($ha > $halim){$ha = $halim;}
#  }

  ($nat,$uni) = (0,0);
  $ha = $ha*pi/12;
  foreach my $i (0..$n){
    $h = $ha*$i/$n;
    my $cosha = cos($h);
    $sinel=$sinl*$sind+$cosl*$cosd*$cosha;
    # tsys seems to come from equation 13.119 of Thompson, Moran and Swenson
    # note that sin(el) = cos(90-el); TM&S ask for sec(z) which is the same as
    # 1/sin(el). The 2.7 is the CMB temperature.
#    $tsys = ($trec+$t0)*exp($tau/$sinel) - $t0 + 2.7;
    $tsys=$trec+$t0*(1-exp(-1*$tau/$sinel))+2.7*exp(-1*$tau/$sinel);
    $uni += $tsys;
    $nat += 1/($tsys*$tsys);
  }
  $uni /= ($n+1);
  $nat /= ($n+1);
  $nat = 1/sqrt($nat);
  return 0.5*($uni+$nat);

}

sub calculate_rms_array {
    my ($rfac,$tsys_ref,$efficiency,$dishdiameter,$totalbw,
	$effbw,$tint,$nbl,$polproductscombined,$centrefreq,@ants)=@_;
    
    my %tsys=%{$tsys_ref};
    # the RMS equation comes directly from AT technical document AT/01.17/025,
    # and assumes that for CABB (an 8-bit correlator) that the correlator efficiency
    # is 1, and that Stokes I is being made (ie. data from both linear polarisations
    # are being combined).
    my $low_freq=$centrefreq-$totalbw/2;
    my $high_freq=$centrefreq+$totalbw/2;
    print "total bw = $totalbw, channel bw = $effbw<br />\n";
    my $nchans=$totalbw/$effbw;
    my @rms;
    my @systemps;
    my @rms_n;
    for (my $i=0;$i<=$#ants;$i++){
	my @systemp;
	my @freq;
	if ($tsys{"tsys_ca0$ants[$i]"}){
	    my @systemp=@{$tsys{"tsys_ca0$ants[$i]"}};
	    my @freq=@{$tsys{"tsys_ca0$ants[$i]"}};
	} else {
	    next;
	}
	for (my $j=0;$j<$nchans;$j++){
	    my $chanfreq_low=$low_freq+$j*$effbw;
	    my $chanfreq_high=$low_freq+($j+1)*$effbw;
	    for (my $k=0;$k<=$#freq;$k++){
		if (($freq[$k]>=$chanfreq_low)&&
		    ($freq[$k]<$chanfreq_high)){
		    $rms[$j]+=$systemp[$k];
		    $rms_n[$j]++;
		}
	    }
	}
    }
    for (my $i=0;$i<$nchans;$i++){
	if ($rms_n[$i]>0){
	    $rms[$i]/=$rms_n[$i];
	    $systemps[$i]=$rms[$i];
	    $rms[$i]*=300.0*$rfac/($efficiency*($dishdiameter**2)*
				   sqrt($effbw*$tint*$nbl*$polproductscombined));
	} else {
	    splice @rms,$i,1;
	    splice @rms_n,$i,1;
	    $i--;
	}
    }

#    my $rms=300.0*$rfac*$tsys/($efficiency*($dishdiameter**2)*
#			       sqrt($effbw*$tint*$nbl*$polproductscombined));
#    return $rms;
    my $av_tsys=&calc_average(@systemps);
    return ($av_tsys,@rms);
}

sub calculate_rms {
    my ($rfac,$tsys,$efficiency,$dishdiameter,
	$effbw,$tint,$nbl,$polproductscombined)=@_;
    
    # the RMS equation comes directly from AT technical document AT/01.17/025,
    # and assumes that for CABB (an 8-bit correlator) that the correlator efficiency
    # is 1, and that Stokes I is being made (ie. data from both linear polarisations
    # are being combined).
    my $rms=300.0*$rfac*$tsys/($efficiency*($dishdiameter**2)*
			       sqrt($effbw*$tint*$nbl*$polproductscombined));
    return $rms;
}

sub calculate_systemsens {
    my ($dishdiameter,$nantsused,$tsys,$efficiency)=@_;

    # the system sensitivity equation comes from AT technical document AT/01.17/025,
    # but has 3514 instead of 3.5 x 10^3 at the beginning of the equation. JS changed
    # this equation to have the antenna diameter as the effective diameter of all
    # antennae combined, instead of just one antenna.
    my $effectivediameter=$dishdiameter*sqrt($nantsused); # do the algebra, it reduces
                                                          # to this
    my $ssen_single=3514*$tsys/($efficiency*($dishdiameter**2));
    my $ssen_all=3514*$tsys/($efficiency*($effectivediameter**2));

    return($ssen_single,$ssen_all);
}

sub calculate_btsens {
    my ($rms,$wavesq,$res1,$res2)=@_;

    # the brightness temperature sensitivity comes from AT technical document
    # AT/01.17/025, but has 1.36 instead of 1.46 (why? I don't know). Other than that
    # this equation doesn't actually have fudge factors :)
    my $bt=1.36*$rms*$wavesq/($res1*$res2);

    return $bt;
}

sub calc_average {
    my @array=@_;

    my $sum=0;
    for (my $i=0;$i<=$#array;$i++){
	$sum+=$array[$i];
    }
    $sum/=($#array+1);

    return $sum;
}
