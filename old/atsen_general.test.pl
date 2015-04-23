#!/usr/bin/perl

use strict;
use CGI;

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
#  30-Nov-2010  Jamie Stevens   Added some convenience functions for getting
#                               4 GHz continuum values and zoom band frequency
#                               specific values.

# Bugs:
#  - The resolution in the DEC direction for hybrid arrays is
#    very simplistic.
#  - No account is made of shadowing in the compact configurations,
#    or of the source being below the elevation limit.

#### main program loop begins
my $in = CGI->new;
my %form = $in->Vars;
# DEBUGGING CODE
$form{'configuration'}="6km";
$form{'frequency'}="9000";
$form{'dec'}="-70";
$form{'ellimit'}="20";
$form{'halimit'}="6";
$form{'bandwidth'}="CFB64M";
$form{'weight'}="N";
#$form{'s_zoom'}="1400";
#$form{'integration'}="720";
$form{'target'}="0.01";
$form{'target-band'}="continuum";
$form{'target-weather'}="poor";
$form{'useca06'}="yes";
$form{'boxcar'}="1";
$form{'zooms'}="1";
$form{'selfgen'}="1";
$form{'rfi'}="1";
$form{'edge'}="100";
#$form{'restfrequency'}="1.420405752";

print $in->header('text/json');
# create the results part of the web page
&call_program(%form);

#### main program loop ends

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

sub call_program {
    my (%form)=@_;

    # determine a random name for the output plot
    my $randstring_length=7;
    my $randstring=&rand_nums($randstring_length);
    my $path_to_stuff="/var/www/vhosts/www.narrabri.atnf.csiro.au/cgi-bin/obstools";
    if (!-d $path_to_stuff) {
	$path_to_stuff = "/home/jstevens/usr/src/atcacode/namoi_web";
    }
    my $spect_filename="rms_plots/rms_spectrum_".$randstring;

    # call the command line version to get the results
    my $sens_command=$path_to_stuff."/atsen_commandline_askap -j ".
	"-c ".$form{"configuration"}." ".
	"-f ".$form{"frequency"}." ".
	"-d ".$form{"dec"}." ".
	"-e ".$form{"ellimit"}." ".
	"-a ".$form{"halimit"}." ".
	"-b ".$form{"bandwidth"}." ".
	"-w ".$form{"weight"}." ".
	"-o ".$spect_filename." ";
    if (defined $form{"integration"}) {
	$sens_command.="-t ".$form{"integration"}." ";
    }
    if (defined $form{"s_zoom"}) {
	$sens_command.="-z ".$form{"s_zoom"}." ";
    }
    if (defined $form{"fourcm"}) {
	$sens_command.="-n ".$form{"fourcm"}." ";
    }
    if ($form{"useca06"} eq "yes"){
	$sens_command.="-6 ";
    }
    if ($form{"4ghz"} eq "yes"){
	$sens_command.="-4";
    }
    if (defined $form{"boxcar"}) {
	$sens_command.="-s ".$form{"boxcar"}." ";
    }
    if (defined $form{"zooms"}) {
	$sens_command.="-C ".$form{"zooms"}." ";
    }
    if (defined $form{"restfrequency"}) {
	$sens_command.="-r ".$form{"restfrequency"}." ";
    }
    if (defined $form{"selfgen"}) {
	$sens_command.="-x ";
    }
    if (defined $form{"rfi"}) {
	$sens_command.="-R ";
    }
    if (defined $form{"edge"}) {
	$sens_command.="-g ".$form{"edge"}." ";
    }
    if (defined $form{"target"}) {
	$sens_command.="-T ".$form{"target"}." ";
    }
    if (defined $form{"target-band"}) {
	if ($form{"target-band"} eq "continuum") {
	    $sens_command.="-1 ";
	} elsif ($form{"target-band"} eq "spectrum") {
	    $sens_command.="-2 ";
	} elsif ($form{"target-band"} eq "zoom") {
	    $sens_command.="-3 ";
	} elsif ($form{"target-band"} eq "specific") {
	    $sens_command.="-4 ";
	}
    }
    if (defined $form{"target-kelvin"}) {
	$sens_command.="-5 ";
    }
    if (defined $form{"target-weather"}) {
	if ($form{"target-weather"} eq "good") {
	    $sens_command.="-7 ";
	} elsif ($form{"target-weather"} eq "average") {
	    $sens_command.="-8 ";
	} elsif ($form{"target-weather"} eq "poor") {
	    $sens_command.="-9 ";
	}
    }
    print $sens_command."\n";
    open(SENSCALC,"-|")||exec $sens_command;
    while(<SENSCALC>){
	chomp;
	my $line=$_;
	print $line."\n";
    }
    close(SENSCALC);

}
