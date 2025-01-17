#!/usr/bin/perl -w

# Copyright 2018 Oliver Lewald, olewald64@gmail.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


##########################################################################
# Modules
##########################################################################

use LoxBerry::System;
use LoxBerry::Web;
use LoxBerry::Log;
use LoxBerry::Storage;
use LoxBerry::IO;
use LoxBerry::JSON;

use CGI::Carp qw(fatalsToBrowser);
use CGI qw/:standard/;
use CGI;
use LWP::Simple;
use LWP::UserAgent;
use File::HomeDir;
use Cwd 'abs_path';
use Scalar::Util qw/reftype/;
use JSON qw( decode_json );
use utf8;
use warnings;
use strict;
use Data::Dumper;
#use Config::Simple '-strict';
#no strict "refs"; # we need it for template system

##########################################################################
# Generic exception handler
##########################################################################

# Every non-handled exceptions sets the @reason variable that can
# be written to the logfile in the END function

$SIG{__DIE__} = sub { our @reason = @_ };

##########################################################################
# Variables
##########################################################################

my $template_title;
my $saveformdata = 0;
my $do = "form";
my $helplink;
my $maxzap;
my $helptemplate;
my $i;
our $lbv;
our $countplayers;
our $rowssonosplayer;
our $miniserver;
our $template;
our $content;
our %navbar;
our $mqttcred;
our $cfgm;

my $helptemplatefilename		= "help/help.html";
my $languagefile 				= "sonos.ini";
my $maintemplatefilename	 	= "sonos.html";
my $pluginconfigfile 			= "sonos.cfg";
my $pluginplayerfile 			= "player.cfg";
my $pluginlogfile				= "sonos.log";
# my $XML_file					= "VIU_Sonos_UDP.xml";
my $lbip 						= LoxBerry::System::get_localip();
my $lbport						= lbwebserverport();
my $ttsfolder					= "tts";
my $mp3folder					= "mp3";
my $urlfile						= "https://raw.githubusercontent.com/Liver64/LoxBerry-Sonos/master/webfrontend/html/release/info.txt";
my $log 						= LoxBerry::Log->new ( name => 'Sonos UI', filename => $lbplogdir ."/". $pluginlogfile, append => 1, addtime => 1 );
my $plugintempplayerfile	 	= "tmp_player.json";
my $scanzonesfile	 			= "network.php";
my $udp_file	 				= "ms_inbound.php";
my $azureregion					= "westeurope"; # Change here if you have a Azure API key for diff. region
my $helplink 					= "http://www.loxwiki.eu/display/LOXBERRY/Sonos4Loxone";
our $error_message				= "";

my $configfile 					= "s4lox_config.json";
my $jsonobj 					= LoxBerry::JSON->new();
our $cfg 						= $jsonobj->open(filename => $lbpconfigdir . "/" . $configfile, writeonclose => 0);

# Set new config options for upgrade installations

# add new parameter for cachesize
if (!defined $cfg->{"MP3"}->{cachesize}) {
	$cfg->{MP3}->{cachesize} = "100";
} 
# Rampto Volume
if ($cfg->{TTS}->{volrampto} eq '')  {
	$cfg->{TTS}->{volrampto} = "25";
}
# Rampto type
if ($cfg->{TTS}->{rampto} eq '')  {
	$cfg->{TTS}->{rampto} = "auto";
}
# add new parameter for Volume correction
if (!defined $cfg->{TTS}->{correction})  {
	$cfg->{TTS}->{correction} = "8";
}
# add new parameter for Azure TTS"
if (!defined $cfg->{TTS}->{regionms})  {
	$cfg->{TTS}->{regionms} = $azureregion;
	$jsonobj->write();
}
# add new parameter for Volume phonemute
if (!defined $cfg->{TTS}->{phonemute})  {
	$cfg->{TTS}->{phonemute} = "8";
}
# add new parameter for waiting time in sec.
if (!defined $cfg->{TTS}->{waiting})  {
	$cfg->{TTS}->{waiting} = "10";
}
# add new parameter for phonestop
if (!defined $cfg->{VARIOUS}->{phonestop})  {
	$cfg->{VARIOUS}->{phonestop} = "0";
}
# Function for zapzone
if (!defined $cfg->{VARIOUS}->{selfunction})  {
	$cfg->{VARIOUS}->{selfunction} = "nextradio";
}
# Reset Time for zapzone
if (!defined $cfg->{VARIOUS}->{cron})  {
	$cfg->{VARIOUS}->{cron} = "1";
}
# checkonline
if ($cfg->{SYSTEM}->{checkt2s} eq '')  {
	$cfg->{SYSTEM}->{checkt2s} = "false";
}
# maxVolume
if (!defined $cfg->{VARIOUS}->{volmax})  {
	$cfg->{VARIOUS}->{volmax} = "0";
}
# Loxdaten an MQTT
if (!defined $cfg->{LOXONE}->{LoxDatenMQTT})  {
	$cfg->{LOXONE}->{LoxDatenMQTT} = "false";
}
# text-to-speech Status
if (!defined $cfg->{TTS}->{t2son})  {
	$cfg->{TTS}->{t2son} = "true";
}
# Starttime TV Monitoring
if (!defined $cfg->{VARIOUS}->{starttime})  {
	$cfg->{VARIOUS}->{starttime} = "7";
}
# Endtime TV Monitoring
if (!defined $cfg->{VARIOUS}->{endtime})  {
	$cfg->{VARIOUS}->{endtime} = "22";
}
# copy old API-key value to apikey
if (defined $cfg->{TTS}->{'API-key'})  {
	$cfg->{TTS}->{apikey} = $cfg->{TTS}->{'API-key'};
	delete $cfg->{TTS}->{'API-key'};
}
# copy global API-key to engine-API-key
if (!defined $cfg->{TTS}->{apikeys}) {
	$cfg->{TTS}->{apikeys}->{$cfg->{TTS}->{t2s_engine}} = $cfg->{TTS}->{apikey};
}
# copy old secret-key value to secretkey
if (defined $cfg->{TTS}->{'secret-key'})  {
	$cfg->{TTS}->{secretkey} = $cfg->{TTS}->{'secret-key'};
	delete $cfg->{TTS}->{'secret-key'};
}
# copy global Secret-key to engine-secretkey
if (!defined $cfg->{TTS}->{secretkeys}) {
	$cfg->{TTS}->{secretkeys}->{$cfg->{TTS}->{t2s_engine}} = $cfg->{TTS}->{secretkey};
}
$jsonobj->write();
	

##########################################################################
# Read Settings
##########################################################################

# read language
my $lblang = lblanguage();
our %SL = LoxBerry::System::readlanguage($template, $languagefile);

# Read Plugin Version
my $sversion = LoxBerry::System::pluginversion();

# Read LoxBerry Version
my $lbversion = LoxBerry::System::lbversion();
#LOGDEB "Loxberry Version: " . $lbversion;

# read all POST-Parameter in namespace "R".
my $cgi = CGI->new;
$cgi->import_names('R');

# Get MQTT Credentials
$mqttcred = LoxBerry::IO::mqtt_connectiondetails();

LOGSTART "Sonos UI started";



#########################################################################
# Parameter
#########################################################################

#$saveformdata = defined $R::saveformdata ? $R::saveformdata : undef;
#$do = defined $R::do ? $R::do : "form";

##
#AJAX Subs
##
if ($R::getkeys)
{
	getkeys();
}

##########################################################################
# Init Main Template
##########################################################################
inittemplate();

##########################################################################
# Set LoxBerry SDK to debug in plugin is in debug
##########################################################################

if($log->loglevel() eq "7") {
	$LoxBerry::System::DEBUG 	= 1;
	$LoxBerry::Web::DEBUG 		= 1;
	$LoxBerry::Storage::DEBUG	= 1;
	$LoxBerry::Log::DEBUG		= 1;
	$LoxBerry::IO::DEBUG		= 1;
}


##########################################################################
# Language Settings
##########################################################################

$template->param("LBHOSTNAME", lbhostname());
$template->param("LBLANG", $lblang);
$template->param("SELFURL", $ENV{REQUEST_URI});

LOGDEB "Read main settings from " . $languagefile . " for language: " . $lblang;

#************************************************************************

# übergibt Plugin Verzeichnis an HTML
$template->param("PLUGINDIR" => $lbpplugindir);

# übergibt Log Verzeichnis und Dateiname an HTML
$template->param("LOGFILE" , $lbplogdir . "/" . $pluginlogfile);

##########################################################################
# check if config files exist and they are readable
##########################################################################

# Check if config file exist

if (!-r $lbpconfigdir . "/" . $configfile) 
{
	LOGCRIT "Plugin config file does not exist";
	$error_message = $SL{'ERRORS.ERR_CHECK_SONOS_CONFIG_FILE'};
	notify($lbpplugindir, "Sonos UI ", "Error loading Sonos configuration file. Please try again or check config folder!", 1);
	&error; 
} else {
	LOGDEB "The Sonos config file has been loaded";
}

LOGDEB "Loxberry Version: " . $lbversion;
$lbv = substr($lbversion,0,1);


##########################################################################
# Main program
##########################################################################


#our %navbar;
$navbar{1}{Name} = "$SL{'BASIS.MENU_SETTINGS'}";
$navbar{1}{URL} = './index.cgi';
$navbar{2}{Name} = "$SL{'BASIS.MENU_OPTIONS'}";
$navbar{2}{URL} = './index.cgi?do=details';
$navbar{99}{Name} = "$SL{'BASIS.MENU_LOGFILES'}";
$navbar{99}{URL} = './index.cgi?do=logfiles';

# if MQTT credentials are valid and Communication turned ON --> insert navbar
if ($mqttcred and $cfg->{LOXONE}->{LoxDaten} eq "true")  {
	$navbar{3}{Name} = "$SL{'BASIS.MENU_MQTT'}";
	# Lower then LB Version 3
	if($lbv < 3)  {
		my $cfgfile = $lbhomedir.'/config/plugins/mqttgateway/mqtt.json';
		my $json = LoxBerry::JSON->new();
		our $cfgm = $json->open(filename => $cfgfile);
		$navbar{3}{URL} = '/admin/plugins/mqttgateway/index.cgi';
	} else {
		my $cfgfile = $lbhomedir.'/config/system/mqttgateway.json';
		my $json = LoxBerry::JSON->new();
		our $cfgm = $json->open(filename => $cfgfile);
		$navbar{3}{URL} = '/admin/system/mqtt.cgi';
	}
	$navbar{3}{target} = '_blank';
}

if ($R::saveformdata1) {
	$template->param( FORMNO => 'form' );
	&save;
}
if ($R::saveformdata2) {
	$template->param( FORMNO => 'details' );
	&save_details;
}

# check if config already saved, if not highlight header text in RED
my $countplayer;
my %configzones = $cfg->{sonoszonen};	

foreach my $key (keys %configzones) {
	$countplayer++;
}
if ( $countplayer < 1 ) {
	$countplayer = 0;
} else {
	$countplayer = 1;
}
$template->param("PLAYERAVAILABLE", $countplayer);


if(!defined $R::do or $R::do eq "form") {
	$navbar{1}{active} = 1;
	$template->param("SETTINGS", "1");
	&form;
} elsif($R::do eq "details") {
	$navbar{2}{active} = 1;
	$template->param("DETAILS", "1");
	&form;
} elsif ($R::do eq "logfiles") {
	LOGTITLE "Show logfiles";
	$navbar{99}{active} = 1;
	$template->param("LOGFILES", "1");
	$template->param("LOGLIST_HTML", LoxBerry::Web::loglist_html());
	printtemplate();
} elsif ($R::do eq "scan") {
	&attention_scan;
} elsif ($R::do eq "scanning") {
	LOGTITLE "Execute Scan";
	&scan;
	$template->param("SETTINGS", "1");
	&form;
} 

$error_message = "Invalid do parameter: ".$R::do;
&error;
exit;



#####################################################
# Form-Sub
#####################################################

sub form 
{
	$template->param( FORMNO => 'FORM' );
	
	# check if path exist (upgrade from v3.5.1)
	if ($cfg->{SYSTEM}->{path} eq "")   {
		$cfg->{SYSTEM}->{path} = "$lbpdatadir";
		$jsonobj->write();
		LOGINF("default path has been added to config");
	}
	
	# prepare Storage
	my $storage = LoxBerry::Storage::get_storage_html(
					formid => 'STORAGEPATH', 
					currentpath => $jsonobj->param("SYSTEM.path"),
					custom_folder => 1,
					type_all => 1, 
					readwriteonly => 1, 
					data_mini => 1,
					label => "$SL{'T2S.SAFE_DETAILS'}");
					
	$template->param("STORAGEPATH", $storage);
	
	#if ($mqttcred && $cfg->{LOXONE}->{LoxDatenMQTT} eq "true")  {
	#	$cfg->{LOXONE}->{LoxPort} = $cfgm->{Main}->{udpport};
	#}

	# read info file from Github and save in $info
	my $info 		= get($urlfile);
	$template		->param("INFO" 			=> "$info");
	
	if ($cfg->{SYSTEM}->{path} eq "")   {
		$cfg->{SYSTEM}->{path} = "$lbpdatadir";
		$jsonobj->write();
	}
			
	# fill saved values into form
	$template		->param("SELFURL", $SL{REQUEST_URI});
	$template		->param("T2S_ENGINE" 	=> $cfg->{TTS}->{t2s_engine}); 
	$template		->param("APIKEY"	=> $cfg->{TTS}->{apikeys}->{$cfg->{TTS}->{t2s_engine}});
	$template		->param("SECKEY"	=> $cfg->{TTS}->{secretkeys}->{$cfg->{TTS}->{t2s_engine}});
	$template		->param("VOICE" 		=> $cfg->{TTS}->{voice});
	$template		->param("CODE" 			=> $cfg->{TTS}->{messageLang});
	$template		->param("DATADIR" 		=> $cfg->{SYSTEM}->{path});
	$template		->param("LOX_ON" 		=> $cfg->{LOXONE}->{LoxDaten});
		
	# Load saved values for "select"
	my $t2s_engine		  = $cfg->{TTS}->{t2s_engine};
	my $rmpvol	 	  	  = $cfg->{TTS}->{volrampto};
	my $storepath 		  = $cfg->{SYSTEM}->{path};
	
	# read Radiofavorites
	our $countradios = 0;
	our $rowsradios;
	my $radiofavorites = $cfg->{RADIO}->{radio};

	foreach my $key (keys %{$radiofavorites}) {
		$countradios++;
		my @fields = split(/,/,$cfg->{RADIO}->{radio}->{$countradios} );
		$rowsradios .= "<tr><td style='height: 25px; width: 43px;' class='auto-style1'><INPUT type='checkbox' style='width: 20px' name='chkradios$countradios' id='chkradios$countradios' align='center'/></td>\n";
		$rowsradios .= "<td style='height: 28px'><input type='text' id='radioname$countradios' name='radioname$countradios' size='20' value='$fields[0]' /> </td>\n";
		$rowsradios .= "<td style='width: 600px; height: 28px'><input type='text' id='radiourl$countradios' name='radiourl$countradios' size='100' value='$fields[1]' style='width: 100%' /> </td>\n";
		$rowsradios .= "<td style='width: 600px; height: 28px'><input type='text' id='coverurl$countradios' name='coverurl$countradios' size='100' value='$fields[2]' style='width: 100%' /> </td></tr>\n";
	}

	if ( $countradios < 1 ) {
		$rowsradios .= "<tr><td colspan=4>" . $SL{'RADIO.SONOS_EMPTY_RADIO'} . "</td></tr>\n";
	}
	LOGDEB "Radio Stations has been loaded.";
	$rowsradios .= "<input type='hidden' id='countradios' name='countradios' value='$countradios'>\n";
	$template->param("ROWSRADIO", $rowsradios);
	
	# *******************************************************************************************************************
	# Player einlesen
	
	our $rowssonosplayer;
	
	my $error_volume = $SL{'T2S.ERROR_VOLUME_PLAYER'};
	my $filename;
	my $config = $cfg->{sonoszonen};
		
	foreach my $key (keys %{$config}) {
		$countplayers++;
		my $room = $key;
		$filename = $lbphtmldir.'/images/icon-'.$config->{$key}->[7].'.png';
		our $statusfile = $lbpdatadir.'/PlayerStatus/s4lox_on_'.$room.'.txt';
		
		$rowssonosplayer .= "<tr><td style='height: 25px; width: 4%;' class='auto-style1'><input type='checkbox' name='chkplayers$countplayers' id='chkplayers$countplayers' align='center'/></td>\n";
		if (-e $statusfile) {
			$rowssonosplayer .= "<td style='height: 28px; width: 16%;'><input type='text' class='pd-price' id='zone$countplayers' name='zone$countplayers' size='40' readonly='true' value='$room' style='width: 100%; background-color: #6dac20;'></td>\n";
		} else {
			$rowssonosplayer .= "<td style='height: 28px; width: 16%;'><input type='text' id='zone$countplayers' name='zone$countplayers' size='40' readonly='true' value='$room' style='width: 100%; background-color: #e6e6e6;'></td>\n";
		}	
		$rowssonosplayer .= "<td style='height: 25px; width: 4%;' class='auto-style1'><input type='checkbox' class='chk-checked' name='mainchk$countplayers' id='mainchk$countplayers' value='$config->{$key}->[6]' align='center'></td>\n";
		$rowssonosplayer .= "<td style='height: 28px; width: 15%;'><input type='text' id='model$countplayers' name='model$countplayers' size='30' readonly='true' value='$config->{$key}->[2]' style='width: 100%; background-color: #e6e6e6;'></td>\n";
		# Column Sonos Player Logo
		if (-e $filename) {
			$rowssonosplayer .= "<td style='height: 28px; width: 2%;'><img src='/plugins/$lbpplugindir/images/icon-$config->{$key}->[7].png' border='0' width='50' height='50' align='middle'/></td>\n";
		} else {
			$rowssonosplayer .= "<td style='height: 28px; width: 2%;'><img src='/plugins/$lbpplugindir/images/sonos_logo_sm.png' border='0' width='50' height='50' align='middle'/></td>\n";
		}
		$rowssonosplayer .= "<td style='height: 28px; width: 17%;'><input type='text' id='ip$countplayers' name='ip$countplayers' size='30' value='$config->{$key}->[0]' style='width: 100%; background-color: #e6e6e6;'></td>\n";
		# Column Pic green/red
		if (exists($config->{$key}[11]) and is_enabled($config->{$key}[11]))   {
			if (exists($config->{$key}[12]) and is_enabled($config->{$key}[12]))   {
				$rowssonosplayer .= "<td style='height: 30px; width: 30px; align: 'middle'><div style='text-align: center;'><img src='/plugins/$lbpplugindir/images/green.png' border='0' width='26' height='28' align='center'/></div></td>\n";
			} else {
				$rowssonosplayer .= "<td style='height: 30px; width: 30px; align: 'middle'><div style='text-align: center;'><img src='/plugins/$lbpplugindir/images/yellow.png' border='0' width='26' height='28' align='center'/></div></td>\n";
			}
		} else {
			$rowssonosplayer .= "<td style='height: 30px; width: 30px; align: 'middle'><div style='text-align: center;'><img src='/plugins/$lbpplugindir/images/red.png' border='0' width='26' height='28' align='center'/></div></td>\n";
		}
		$rowssonosplayer .= "<td style='width: 10%; height: 28px;'><input type='text' id='t2svol$countplayers' size='100' data-validation-rule='special:number-min-max-value:1:100' data-validation-error-msg='$error_volume' name='t2svol$countplayers' value='$config->{$key}->[3]'></td>\n";
		$rowssonosplayer .= "<td style='width: 10%; height: 28px;'><input type='text' id='sonosvol$countplayers' size='100' data-validation-rule='special:number-min-max-value:1:100' data-validation-error-msg='$error_volume' name='sonosvol$countplayers' value='$config->{$key}->[4]'></td>\n";
		$rowssonosplayer .= "<td style='width: 10%; height: 28px;'><input type='text' id='maxvol$countplayers' size='100' data-validation-rule='special:number-min-max-value:1:100' data-validation-error-msg='$error_volume' name='maxvol$countplayers' value='$config->{$key}->[5]'></td>\n";
		# Column Soundbar Volume
		if (exists($config->{$key}[13]))   {
			$rowssonosplayer .= "<td style='width: 10%; height: 28px;'><div class='tvmonitorsecond'><input type='text' id='tvvol$countplayers' size='100' data-validation-rule='special:number-min-max-value:1:100' data-validation-error-msg='$error_volume' name='tvvol$countplayers' value='$config->{$key}->[14]'></div></td>\n";
			$rowssonosplayer .= "<input type='hidden' id='sb$countplayers' name='sb$countplayers' value='$config->{$key}->[13]'>\n";
		} else {
			$rowssonosplayer .= "</tr>";
		}
		$rowssonosplayer .= "<input type='hidden' id='room$countplayers' name='room$countplayers' value=$room>\n";
		$rowssonosplayer .= "<input type='hidden' id='models$countplayers' name='models$countplayers' value='$config->{$key}->[7]'>\n";
		$rowssonosplayer .= "<input type='hidden' id='groupId$countplayers' name='groupId$countplayers' value='$config->{$key}->[8]'>\n";
		$rowssonosplayer .= "<input type='hidden' id='householdId$countplayers' name='householdId$countplayers' value='$config->{$key}->[9]'>\n";
		$rowssonosplayer .= "<input type='hidden' id='deviceId$countplayers' name='deviceId$countplayers' value='$config->{$key}->[10]'>\n";
		$rowssonosplayer .= "<input type='hidden' id='audioclip$countplayers' name='audioclip$countplayers' value='$config->{$key}->[11]'>\n";
		$rowssonosplayer .= "<input type='hidden' id='voice$countplayers' name='voice$countplayers' value='$config->{$key}->[12]'>\n";
		$rowssonosplayer .= "<input type='hidden' id='rincon$countplayers' name='rincon$countplayers' data-validation-rule='special:number-min-max-value:1:100' data-validation-error-msg='$error_volume' value='$config->{$key}->[1]'>\n";
	}
	
	LOGDEB "Sonos players has been loaded.";					
	
	if ( $countplayers < 1 ) {
		$rowssonosplayer .= "<tr><td colspan=10>" . $SL{'ZONES.SONOS_EMPTY_ZONES'} . "</td></tr>\n";
	}
	$rowssonosplayer .= "<input type='hidden' id='countplayers' name='countplayers' value='$countplayers'>\n";
	$template->param("ROWSSONOSPLAYER", $rowssonosplayer);
	
	# *******************************************************************************************************************
	# Get Miniserver
	my $mshtml = LoxBerry::Web::mslist_select_html( 
							FORMID => 'ms',
							SELECTED => $jsonobj->{LOXONE}->{Loxone}, 
							DATA_MINI => 1,
							LABEL => "",
							);
	$template->param('MS', $mshtml);
		
	LOGDEB "List of available Miniserver(s) has been successful loaded";
	# *******************************************************************************************************************
		
	# fill dropdown with list of files from tts/mp3 folder
	my $dir = $lbpdatadir.'/'.$ttsfolder.'/'.$mp3folder.'/';
	my $mp3_list;
	
    opendir(DIR, $dir) or die $!;
	my @dots 
        = grep { 
            /\.mp3$/      # just files ending with .mp3
	    && -f "$dir/$_"   # and is a file
	} 
	readdir(DIR);
	my @sorted_dots = sort { $a <=> $b } @dots;		# sort files numericly
    # Loop through the array adding filenames to dropdown
    foreach my $file (@sorted_dots) {
		$mp3_list.= "<option value='$file'>" . $file . "</option>\n";
    }
	closedir(DIR);
	$template->param("MP3_LIST", $mp3_list);
	LOGDEB "List of MP3 files has been successful loaded";
	
	# check if MQTT is installed and valid credentials received
	if ($mqttcred)   {
		$template->param("MQTT" => "true");
		LOGDEB "MQTT Gateway is installed and valid credentials received.";
	} else {
		$template->param("MQTT" => "false");
		$cfg->{LOXONE}->{LoxDatenMQTT} = "false";
		$jsonobj->write();
		LOGDEB "MQTT Gateway is not installed or wrong credentials received.";
	}
	
	LOGOK "Sonos Plugin has been successfully loaded.";
	
	# Donation
	if (is_enabled($cfg->{VARIOUS}->{donate})) {
		$template->param("DONATE", 'checked="checked"');
	} else {
		$template->param("DONATE", '');
	}
	printtemplate();
	#$content = $filename;
	#print_test($content);
	exit;
	
}



#####################################################
# Save_details-Sub
#####################################################

sub save_details
{
	my $countradios = param('countradios');
	
	LOGINF "Start writing details configuration file";
	
	$cfg->{TTS}->{volrampto} = "$R::rmpvol";
	$cfg->{TTS}->{rampto} = "$R::rampto";
	$cfg->{TTS}->{correction} = "$R::correction";
	$cfg->{MP3}->{waiting} = "$R::waiting";
	$cfg->{MP3}->{volumedown} = "$R::volume";
	$cfg->{MP3}->{volumeup} = "$R::volume";
	$cfg->{VARIOUS}->{announceradio} = "$R::announceradio";
	$cfg->{VARIOUS}->{announceradio_always} = "$R::announceradio_always";
	$cfg->{VARIOUS}->{phonemute} = "$R::phonemute";
	$cfg->{VARIOUS}->{phonestop} = "$R::phonestop";
	$cfg->{VARIOUS}->{volmax} = "$R::volmax";
	$cfg->{LOCATION}->{town} = "$R::town";
	$cfg->{VARIOUS}->{CALDavMuell} = "$R::wastecal";
	$cfg->{VARIOUS}->{CALDav2} = "$R::cal";
	$cfg->{VARIOUS}->{cron} = "$R::cron";
	$cfg->{VARIOUS}->{selfunction} = "$R::func_list";
	$cfg->{SYSTEM}->{checkt2s} = "$R::checkt2s";
		
	# save all radiostations
	for ($i = 1; $i <= $countradios; $i++) {
		my $rname = param("radioname$i");
		my $rurl = param("radiourl$i");
		my $curl = param("coverurl$i");
		$cfg->{RADIO}->{radio}->{$i} = $rname . "," . $rurl . "," . $curl;
	}
	$jsonobj->write();
	

	  if ($R::cron eq "1") 
	  {
	    system ("ln -s $lbphtmldir/bin/cronjob.sh $lbhomedir/system/cron/cron.01min/$lbpplugindir");
	    unlink ("$lbhomedir/system/cron/cron.03min/$lbpplugindir");
		unlink ("$lbhomedir/system/cron/cron.05min/$lbpplugindir");
	    unlink ("$lbhomedir/system/cron/cron.10min/$lbpplugindir");
	    unlink ("$lbhomedir/system/cron/cron.30min/$lbpplugindir");
		LOGOK "Cron job each Minute created";
	  }
	  if ($R::cron eq "3") 
	  {
	    system ("ln -s $lbphtmldir/bin/cronjob.sh $lbhomedir/system/cron/cron.03min/$lbpplugindir");
	    unlink ("$lbhomedir/system/cron/cron.01min/$lbpplugindir");
		unlink ("$lbhomedir/system/cron/cron.05min/$lbpplugindir");
	    unlink ("$lbhomedir/system/cron/cron.10min/$lbpplugindir");
	    unlink ("$lbhomedir/system/cron/cron.30min/$lbpplugindir");
		LOGOK "Cron job 3 Minutes created";
	  }
	  if ($R::cron eq "5") 
	 {
	    system ("ln -s $lbphtmldir/bin/cronjob.sh $lbhomedir/system/cron/cron.05min/$lbpplugindir");
	    unlink ("$lbhomedir/system/cron/cron.03min/$lbpplugindir");
		unlink ("$lbhomedir/system/cron/cron.01min/$lbpplugindir");
	    unlink ("$lbhomedir/system/cron/cron.10min/$lbpplugindir");
	    unlink ("$lbhomedir/system/cron/cron.30min/$lbpplugindir");
		LOGOK "Cron job 5 Minutes created";
	  }
	  if ($R::cron eq "10") 
	  {
	    system ("ln -s $lbphtmldir/bin/cronjob.sh $lbhomedir/system/cron/cron.10min/$lbpplugindir");
	    unlink ("$lbhomedir/system/cron/cron.03min/$lbpplugindir");
		unlink ("$lbhomedir/system/cron/cron.05min/$lbpplugindir");
	    unlink ("$lbhomedir/system/cron/cron.01min/$lbpplugindir");
	    unlink ("$lbhomedir/system/cron/cron.30min/$lbpplugindir");
		LOGOK "Cron job 10 Minutes created";
	  }
	  if ($R::cron eq "30") 
	  {
	    system ("ln -s $lbphtmldir/bin/cronjob.sh $lbhomedir/system/cron/cron.30min/$lbpplugindir");
	    unlink ("$lbhomedir/system/cron/cron.03min/$lbpplugindir");
		unlink ("$lbhomedir/system/cron/cron.05min/$lbpplugindir");
	    unlink ("$lbhomedir/system/cron/cron.10min/$lbpplugindir");
	    unlink ("$lbhomedir/system/cron/cron.01min/$lbpplugindir");
		LOGOK "Cron job 30 Minutes created";
	  }
	  
	
	#my $file = qx(/usr/bin/php $lbphtmldir/bin/create_config.php);		
	LOGOK "Detail settings has been saved successful";
	&print_save;
	exit;
}

#####################################################
# Save-Sub
#####################################################

sub save 
{
	# Everything from Forms
	my $countplayers	= param('countplayers');
	my $countradios 	= param('countradios');
	my $LoxDaten	 	= param('sendlox');
	my $selminiserver	= param('ms');
	
	# get Miniserver entry from former Versions prior to v3.5.2 (MINISERVER1) and extract last character
	my $sel_ms = substr($selminiserver, -1, 1);
	
	my $gcfg         = new Config::Simple("$lbsconfigdir/general.cfg");
	my $miniservers	= $gcfg->param("BASE.MINISERVERS");
	my $MiniServer	= $gcfg->param("MINISERVER$selminiserver.IPADDRESS");
	my $MSWebPort	= $gcfg->param("MINISERVER$selminiserver.PORT");
	my $MSUser		= $gcfg->param("MINISERVER$selminiserver.ADMIN");
	my $MSPass		= $gcfg->param("MINISERVER$selminiserver.PASS");
			
	# turn on/off MS inbound function 
	if ($LoxDaten eq "true") {
		LOGDEB "Coummunication to Miniserver is switched on";
	} else {
		LOGDEB "Coummunication to Miniserver is switched off.";
	}
		
	# OK - now installing...

	# Write configuration file(s)
	$cfg->{LOXONE}->{Loxone} = "$sel_ms";
	$cfg->{LOXONE}->{LoxDaten} = "$R::sendlox";
	$cfg->{LOXONE}->{LoxDatenMQTT} = "$R::sendloxMQTT";
	if ($R::sendlox eq "true")   {
		if ($R::sendloxMQTT eq "false")  {
			$cfg->{LOXONE}->{LoxPort} = "$R::udpport";
		} else {
			delete $cfg->{LOXONE}->{LoxPort};
		}
	}
	$cfg->{TTS}->{t2s_engine} = "$R::t2s_engine";
	$cfg->{TTS}->{messageLang} = "$R::t2slang";
	$cfg->{TTS}->{apikey} = "$R::apikey";
	$cfg->{TTS}->{apikeys}->{$cfg->{TTS}->{t2s_engine}} = $cfg->{TTS}->{apikey};
	$cfg->{TTS}->{secretkey} = "$R::seckey";
	$cfg->{TTS}->{secretkeys}->{$cfg->{TTS}->{t2s_engine}} = $cfg->{TTS}->{secretkey};
	$cfg->{TTS}->{voice} = "$R::voice";
	$cfg->{TTS}->{regionms} = $azureregion;
	$cfg->{TTS}->{t2son} = "$R::t2son";
	$cfg->{MP3}->{MP3store} = "$R::mp3store";
	$cfg->{MP3}->{cachesize} = "$R::cachesize";
	$cfg->{MP3}->{file_gong} = "$R::file_gong";
	$cfg->{VARIOUS}->{donate} = "$R::donate";
	$cfg->{VARIOUS}->{CALDavMuell} = "$R::wastecal";
	$cfg->{VARIOUS}->{CALDav2} = "$R::cal";
	$cfg->{VARIOUS}->{tvmon} = "$R::tvmon";
	$cfg->{VARIOUS}->{starttime} = "$R::starttime";
	$cfg->{VARIOUS}->{endtime} = "$R::endtime";
	$cfg->{VARIOUS}->{tvmonspeech} = "$R::tvmonspeech";
	$cfg->{VARIOUS}->{tvmonsurr} = "$R::tvmonsurr";
	$cfg->{VARIOUS}->{tvmonnight} = "$R::tvmonnight";
	$cfg->{VARIOUS}->{fromtime} = "$R::fromtime";
	$cfg->{LOCATION}->{region} = "$R::region";
	$cfg->{LOCATION}->{googlekey} = "$R::googlekey";
	$cfg->{LOCATION}->{googletown} = "$R::googletown";
	$cfg->{LOCATION}->{googlestreet} = "$R::googlestreet";
	$cfg->{LOCATION}->{town} = "$R::town";
	$cfg->{SYSTEM}->{mp3path} = "$R::STORAGEPATH/$ttsfolder/$mp3folder";
	$cfg->{SYSTEM}->{ttspath} = "$R::STORAGEPATH/$ttsfolder";
	$cfg->{SYSTEM}->{path} = "$R::STORAGEPATH";
	$cfg->{SYSTEM}->{httpinterface} = "http://$lbip:$lbport/plugins/$lbpplugindir/interfacedownload";
	$cfg->{SYSTEM}->{cifsinterface} = "//$lbip:$lbport/plugindata/$lbpplugindir/interfacedownload";
		
	LOGINF "Start writing settings to configuration file";
	
	# If storage folders does not exist, copy default mp3 files
	my $copy = 0;
	if (!-e "$R::STORAGEPATH/$ttsfolder/$mp3folder") {
		$copy = 1;
	}
	
	LOGINF "Creating folders and symlinks";
	system ("mkdir -p $R::STORAGEPATH/$ttsfolder/$mp3folder");
	system ("mkdir -p $R::STORAGEPATH/$ttsfolder");
	system ("rm $lbpdatadir/interfacedownload");
	system ("rm $lbphtmldir/interfacedownload");
	system ("ln -s $R::STORAGEPATH/$ttsfolder $lbpdatadir/interfacedownload");
	system ("ln -s $R::STORAGEPATH/$ttsfolder $lbphtmldir/interfacedownload");
	LOGOK "All folders and symlinks created successfully.";

	if ($copy) {
		LOGINF "Copy existing mp3 files from $lbpdatadir/$ttsfolder/$mp3folder to $R::STORAGEPATH/$ttsfolder/$mp3folder";
		system ("cp -r $lbpdatadir/$ttsfolder/$mp3folder/* $R::STORAGEPATH/$ttsfolder/$mp3folder");
	}
	
	# save all radiostations
	for ($i = 1; $i <= $countradios; $i++) {
		if ( param("chkradios$i") ) { # if radio should be deleted
			delete $cfg->{RADIO}->{radio}->{$i}  ;
		} else { # save
			my $rname = param("radioname$i");
			my $rurl = param("radiourl$i");
			my $curl = param("coverurl$i");
			$cfg->{RADIO}->{radio}->{$i} = $rname . "," . $rurl . "," . $curl;
		}
	}
	LOGDEB "Radio Stations has been saved.";
	
	# check if scan zones has been executed and min. 1 Player been added
	if ($countplayers < 1)  {
		$error_message = $SL{'ZONES.ERROR_NO_SCAN'};
		&error;
	}
	
	# save all Sonos devices
	my $emergecalltts;
	
	for ($i = 1; $i <= $countplayers; $i++) {
		if ( param("chkplayers$i") ) { # if player should be deleted
			delete $cfg->{sonoszonen}->{param("zone$i")};
		} else { # save
			if (param("mainchk$i") eq "on")   {
				$emergecalltts = "on";
			} else {
				$emergecalltts = "off";
			}
			my @player = (  param("ip$i"), 
							param("rincon$i"), 
							param("model$i"), 
							param("t2svol$i"), 
							param("sonosvol$i"), 
							param("maxvol$i"), 
							$emergecalltts, 
							param("models$i"), 
							param("groupId$i"), 
							param("householdId$i"), 
							param("deviceId$i"), 
							param("audioclip$i"), 
							param("voice$i")
						 );
			if (param("sb$i") eq "SB")   {
				push @player , param("sb$i");
				push @player , param("tvvol$i");
			}
			$cfg->{sonoszonen}->{param("zone$i")} = \@player;
		}
	}
	
	$jsonobj->write();
	LOGDEB "Sonos Zones has been saved.";
	
	# call to prepare XML Template during saving
	if ($R::sendlox eq "true") {
		&prep_XML;
	}
	
	my $tv = qx(/usr/bin/php $lbphtmldir/bin/tv_monitor_conf.php);	
	LOGOK "Main settings has been saved successful";
	
	&print_save;
	my $on = qx(/usr/bin/php $lbphtmldir/bin/check_on_state.php);	
	exit;
	
}



#####################################################
# Scan Sonos Player - Sub
#####################################################

sub scan
{

	my $error_volume = $SL{'T2S.ERROR_VOLUME_PLAYER'};
	
	LOGINF "Scan for Sonos Zones has been executed.";
	
	# executes PHP network.php script (read existing config and add new zones)
	my $response = qx(/usr/bin/php $lbphtmldir/system/$scanzonesfile);
			
	if ($response eq "[]") {
		LOGINF "No new Players has been added to Plugin.";
		return($countplayers);
	} elsif ($response eq "")  {
		$error_message = $SL{'ERRORS.ERR_SCAN'};
		&error;
	} else {
		LOGOK "JSON data from application has been succesfully received.";
		my $config = decode_json($response);
	
		# create table of Sonos devices
		foreach my $key (keys %{$config})
		{
			my $filename = $lbphtmldir.'/images/icon-'.$config->{$key}->[7].'.png';
				
			$countplayers++;
			$rowssonosplayer .= "<tr><td style='height: 25px; width: 4%;' class='auto-style1'><INPUT type='checkbox' style='width: 20px' name='chkplayers$countplayers' id='chkplayers$countplayers' align='center'/></td>\n";
			$rowssonosplayer .= "<td style='height: 28px; width: 16%;'><input type='text' id='zone$countplayers' name='zone$countplayers' size='40' readonly='true' value='$key' style='width: 100%; background-color: #e6e6e6;' /> </td>\n";
			$rowssonosplayer .= "<td style='height: 25px; width: 4%;' class='auto-style1'><DIV class='chk-group'><INPUT type='checkbox' class='chk-checked' name='mainchk$countplayers' id='mainchk$countplayers' value='$config->{$key}->[6]' align='center'/></DIV></td>\n";
			$rowssonosplayer .= "<td style='height: 28px; width: 15%;'><input type='text' id='model$countplayers' name='model$countplayers' size='30' readonly='true' value='$config->{$key}->[2]' style='width: 100%; background-color: #e6e6e6;' /> </td>\n";
			# Column Sonos Player Logo
			if (-e $filename) {
				$rowssonosplayer .= "<td style='height: 28px; width: 2%;'><img src='/plugins/$lbpplugindir/images/icon-$config->{$key}->[7].png' border='0' width='50' height='50' align='middle'/> </td>\n";
			} else {
				$rowssonosplayer .= "<td style='height: 28px; width: 2%;'><img src='/plugins/$lbpplugindir/images/sonos_logo_sm.png' border='0' width='50' height='50' align='middle'/> </td>\n";
			}
			$rowssonosplayer .= "<td style='height: 28px; width: 17%;'><input type='text' id='ip$countplayers' name='ip$countplayers' size='30' value='$config->{$key}->[0]' style='width: 100%; background-color: #e6e6e6;' /> </td>\n";
			# Column Pic green/red
			if ($config->{$key}->[11] and is_enabled($config->{$key}->[11]))   {
				if ($config->{$key}->[12] and is_enabled($config->{$key}->[12]))   {
					$rowssonosplayer .= "<td style='height: 30px; width: 30px; align: 'middle'><div style='text-align: center;'><img src='/plugins/$lbpplugindir/images/green.png' border='0' width='26' height='28' align='center'/></div></td>\n";
				} else {
					$rowssonosplayer .= "<td style='height: 30px; width: 30px; align: 'middle'><div style='text-align: center;'><img src='/plugins/$lbpplugindir/images/yellow.png' border='0' width='26' height='28' align='center'/></div></td>\n";
				}
			} else {
				$rowssonosplayer .= "<td style='height: 30px; width: 30px; align: 'middle'><div style='text-align: center;'><img src='/plugins/$lbpplugindir/images/red.png' border='0' width='26' height='28' align='center'/></div></td>\n";
			}
			$rowssonosplayer .= "<td style='width: 10%; height: 28px;'><input type='text' id='t2svol$countplayers' size='100' data-validation-rule='special:number-min-max-value:1:100' data-validation-error-msg='$error_volume' name='t2svol$countplayers' value='$config->{$key}->[3]'' /> </td>\n";
			$rowssonosplayer .= "<td style='width: 10%; height: 28px;'><input type='text' id='sonosvol$countplayers' size='100' data-validation-rule='special:number-min-max-value:1:100' data-validation-error-msg='$error_volume' name='sonosvol$countplayers' value='$config->{$key}->[4]'' /> </td>\n";
			$rowssonosplayer .= "<td style='width: 10%; height: 28px;'><input type='text' id='maxvol$countplayers' size='100' data-validation-rule='special:number-min-max-value:1:100' data-validation-error-msg='$error_volume' name='maxvol$countplayers' value='$config->{$key}->[5]'' /> </td>\n";
			# Column Soundbar Volume
			if ($config->{$key}->[13])   {
				$rowssonosplayer .= "<input type='hidden' id='sb$countplayers' size='100' name='sb$countplayers' value='$config->{$key}->[13]'>\n";
				$rowssonosplayer .= "<td style='width: 10%; height: 28px;'><input type='text' id='tvvol$countplayers' size='100' data-validation-rule='special:number-min-max-value:1:100' data-validation-error-msg='$error_volume' name='tvvol$countplayers' value='$config->{$key}->[14]'' /> </td> </tr>\n";
			}
			$rowssonosplayer .= "<input type='hidden' id='models$countplayers' name='models$countplayers' value='$config->{$key}->[7]'>\n";
			$rowssonosplayer .= "<input type='hidden' id='groupId$countplayers' name='groupId$countplayers' value='$config->{$key}->[8]'>\n";
			$rowssonosplayer .= "<input type='hidden' id='householdId$countplayers' name='householdId$countplayers' value='$config->{$key}->[9]'>\n";
			$rowssonosplayer .= "<input type='hidden' id='deviceId$countplayers' name='deviceId$countplayers' value='$config->{$key}->[10]'>\n";
			$rowssonosplayer .= "<input type='hidden' id='audioclip$countplayers' name='audioclip$countplayers' value='$config->{$key}->[11]'>\n";
			$rowssonosplayer .= "<input type='hidden' id='voice$countplayers' name='voice$countplayers' value='$config->{$key}->[12]'>\n";
			$rowssonosplayer .= "<input type='hidden' id='rincon$countplayers' name='rincon$countplayers' value='$config->{$key}->[1]'>\n";
		}
		$template->param("ROWSSONOSPLAYER", $rowssonosplayer);
		LOGOK "New Players has been added to Plugin.";
		return($countplayers);
	}
}




#####################################################
# execute PHP script ot generate XML Template - Sub
#####################################################
 
 sub prep_XML
{
	# executes PHP script and saves XML Template local
	my $udp_temp = qx(/usr/bin/php $lbphtmldir/system/$udp_file);
	
	#if (!-r $lbphtmldir . "/system/" . $XML_file) 
	#{
	#	LOGWARN "File '".$XML_file."' has not been generated and could not be downloaded. Please check log file";
	#	return();
	#}
	LOGOK "XML Template files generation has been called";
	return();
}
 

	
#####################################################
# Error-Sub
#####################################################

sub error 
{
	$template->param("ERROR", "1");
	$template_title = $SL{'ERRORS.MY_NAME'} . ": v$sversion - " . $SL{'ERRORS.ERR_TITLE'};
	LoxBerry::Web::lbheader($template_title, $helplink, $helptemplatefilename);
	$template->param('ERR_MESSAGE', $error_message);
	print $template->output();
	LoxBerry::Web::lbfooter();
	exit;
}

sub getkeys
{
	print "Content-type: application/json\n\n";
	my $engine = defined $R::t2s_engine ? $R::t2s_engine : "";
	my $apikey = defined $cfg->{TTS}->{apikeys}->{$engine} ? $cfg->{TTS}->{apikeys}->{$engine} : "";
	my $secret = defined $cfg->{TTS}->{secretkeys}->{$engine} ? $cfg->{TTS}->{secretkeys}->{$engine} : "";
	print "{\"apikey\":\"$apikey\",\"seckey\":\"$secret\"}";
	exit;
}

#####################################################
# Save
#####################################################

sub print_save
{
	$template->param("SAVE", "1");
	$template_title = "$SL{'BASIS.MAIN_TITLE'}: v$sversion";
	LoxBerry::Web::lbheader($template_title, $helplink, $helptemplatefilename);
	print $template->output();
	LoxBerry::Web::lbfooter();
	exit;
}


#####################################################
# Attention Scan Sonos Player
#####################################################

sub attention_scan
{
	LOGDEB "Scan request for Sonos Zones will be executed.";
	$template->param("NOTICE", "1");	
	$template_title = "$SL{'BASIS.MAIN_TITLE'}: v$sversion";
	LoxBerry::Web::lbheader($template_title, $helplink, $helptemplatefilename);
	print $template->output();
	LoxBerry::Web::lbfooter();
	exit;
}
	


##########################################################################
# Init Template
##########################################################################

sub inittemplate
{
	# Check, if filename for the maintemplate is readable, if not raise an error
	stat($lbptemplatedir . "/" . $maintemplatefilename);
	if ( !-r _ )
	{
		$error_message = "Error: Main template not readable";
		LOGCRIT "The ".$maintemplatefilename." file could not be loaded. Abort plugin loading";
		LOGCRIT $error_message;
		&error;
	}
	$template =  HTML::Template->new(
				filename => $lbptemplatedir . "/" . $maintemplatefilename,
				global_vars => 1,
				loop_context_vars => 1,
				die_on_bad_params=> 0,
				associate => $jsonobj,
				%htmltemplate_options,
				debug => 1
				);
	%SL = LoxBerry::System::readlanguage($template, $languagefile);			

}


##########################################################################
# Print Template
##########################################################################

sub printtemplate
{	
	#our $htmlhead = '<link rel="stylesheet" type="text/css" href="css/flipswitch.css" media="screen" />';
	LoxBerry::Web::lbheader("$SL{'BASIS.MAIN_TITLE'}: v$sversion", $helplink, $helptemplate);
	print LoxBerry::Log::get_notifications_html($lbpplugindir);
	print $template->output();
	LoxBerry::Web::lbfooter();
	exit;
}


##########################################################################
# Print for testing
##########################################################################

sub print_test
{
	# Print Template
	print "Content-Type: text/html; charset=utf-8\n\n"; 
	print "*********************************************************************************************";
	print "<br>";
	print " *** Ausgabe zu Testzwecken";
	print "<br>";
	print "*********************************************************************************************";
	print "<br>";
	print "<br>";
	print Dumper($content); 
	exit;
}


##########################################################################
# END routine - is called on every exit (also on exceptions)
##########################################################################
sub END 
{	
	our @reason;
	
	if ($log) {
		if (@reason) {
			LOGCRIT "Unhandled exception catched:";
			LOGERR @reason;
			LOGEND "Finished with an exception";
		} elsif ($error_message) {
			LOGEND "Finished with error: ".$error_message;
		} else {
			LOGEND "Finished successful";
		}
	}
}
