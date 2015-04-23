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
		     -style => [{ -src => '/stylesheets/ca_style.css'},
				{ -src => '/stylesheets/senscalc_style.css'}],
		     -script => [{ -src => 'http://ajax.googleapis.com/ajax/libs/dojo/1.5/dojo/dojo.xd.js' },
				 { -src => '/atsen.js' }]);
    
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
    print "<img src=\"/tooltip_icon.gif\" id=\"tooltip_frequencies\" />";
#	"<div id=\"tooltip_frequencies\" class=\"xstooltip\"><b>Recommended frequencies:</b><br /><b>16cm:</b> 2100 MHz<br />".
#	"<b>6cm:</b> 5500 MHz<br /><b>3cm:</b> 9000 MHz<br /><b>15mm:</b> 17000,19000 MHz<br /><b>7mm:</b> 33000,35000,43000,45000 MHz<br />".
#	"<b>3mm:</b> 93000,95000 MHz</div>";
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
    print " For CABB  it is assumed that the full 2GHz is available at all frequencies.";
    print " RFI may reduce the usable bandwidth,";
    print " particularly at 20/13cm.<br /><br />\n";
    print "It is assumed that the nominated integration time is evenly spread over the period the source is above the set elevation limit.";
    print " Note the time given is the integration time: this does not account for overheads";
    print " involved in calibration. Depending on the calibration scheme used, these overheads might vary between 5% for simple";
    print " 20cm observations, to 50% for 3mm observations.<br /><br />\n";

    print "This page calls a command-line version of the sensitivity calculator to do all the work. You may";
    print " obtain a copy of this calculator from <A HREF=\"/atca_sensitivity_calculator.tar.gz\">this archive</A>.<br /><br />\n";

    print "Page last updated: 11-Oct-2010.<br />\n";
    print "This tool was originally developed by Steven Tingay and Lister Staveley-Smith, and developed further by Bob Sault, Phil Edwards and Jamie Stevens.<br /><br />\n";

    print "</div>\n";

}

sub rand_nums {
    my ($length)=@_;
    my $serial=int(rand(49))+1;
    my %local_cache;
    $local_cache{$serial}=1;
    for (2..$length){
	my $num=int(rand(49))+1;
	redo if exists $local_cache{$num};
	$local_cache{$num}=1;
	$serial.="-$num";
    }
    return $serial;
}

sub present_results {
    my (%form)=@_;

    # begin by making a div to the right of the Inputs div
    print "<div style=\"float: left;\">";
    print h2("Results");

    # determine a random name for the output plot
    my $randstring_length=7;
    my $randstring=&rand_nums($randstring_length);
    my $path_to_stuff="/var/www/vhosts/www.narrabri.atnf.csiro.au/cgi-bin/obstools";
    my $spect_filename="rms_plots/rms_spectrum_".$randstring;

    # call the command line version to get the results
    my $sens_command=$path_to_stuff."/atsen_commandline -H ".
	"-c ".$form{"configuration"}." ".
	"-f ".$form{"frequency"}." ".
	"-d ".$form{"dec"}." ".
	"-e ".$form{"ellimit"}." ".
	"-a ".$form{"halimit"}." ".
	"-b ".$form{"bandwidth"}." ".
	"-w ".$form{"weight"}." ".
	"-t ".$form{"integration"}." ".
	"-o ".$spect_filename." ";
    if ($form{"useca06"} eq "yes"){
	$sens_command.="-6";
    }
#    print "trying to do this:<br />";
#    print $sens_command."<br />\n";
    open(SENSCALC,"-|")||exec $sens_command;
    while(<SENSCALC>){
	chomp;
	my $line=$_;
	print $line."\n";
    }
    close(SENSCALC);

    # attach the rms spectrum plot
    $spect_filename.=".png";
    print "<br /><img src=\"/".$spect_filename."\" />\n";

    # end the div
    print "</div>\n";

}
