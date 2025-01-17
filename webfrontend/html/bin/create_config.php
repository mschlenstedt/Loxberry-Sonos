<?php

require_once "loxberry_system.php";
require_once "loxberry_log.php";

echo "<PRE>";
	
$version = LBSystem::pluginversion();

# if function called directly by URL then overwrite actual LB Version to lower in order to execute script
$call = "false";
$syntax = $_SERVER['REQUEST_URI'];
$pos = strrpos($syntax, "/");
$rest = substr($syntax, $pos+1, $pos+20); 
If ($rest == "create_config.php")    {
	$version = "5.3.8";
	$call = "true";
}

	
If ($version < "5.4.0")   {
	create_JSON_config();
	echo "<OK> New JSON configuration file required. Your actual Version is: v".LBSystem::pluginversion()."".PHP_EOL;
	LOGOK("bin/create_config.php: New JSON configuration file required. Your actual Version is: v".$version);
} else {
	echo "<INFO> The JSON configuration is up-to-date, nothing to do :-)".PHP_EOL;
	LOGINF("bin/create_config.php: The JSON configuration is up-to-date, nothing to do.");
}


function create_JSON_config()    {
	
	global $lbpconfigdir, $call;
	
	$configfile	= $lbpconfigdir."/s4lox_config.json";	
	
	// Parsen der Konfigurationsdatei sonos.cfg
	if (!is_file($lbpconfigdir.'/sonos.cfg')) {
		LOGWARN('bin/create_config.php: The file sonos.cfg could not be opened, please try again!', 4);
	} else {
		try {
			$tmpsonos = parse_ini_file($lbpconfigdir.'/sonos.cfg', TRUE, INI_SCANNER_RAW);
			if ($tmpsonos === false)  {
				LOGERR('bin/create_config.php: The file sonos.cfg could not be parsed, the file may be disruppted. Please check/save your Plugin Config or check file "sonos.cfg" manually!');
				exit(1);
			}
			LOGDEB("bin/create_config.php: Sonos config has been loaded");
		} catch (Exception $e) {
			LOGWARN("bin/create_config.php: The file sonos.cfg has been parsed with errors, plesae check your settings and/or check file 's4lox_config.json'");
		}
			
	}
	// Parsen der Sonos Zonen Konfigurationsdatei player.cfg
	if (!is_file($lbpconfigdir.'/player.cfg')) {
		LOGWARN('bin/create_config.php: The file player.cfg could not be opened, please try again!', 4);
	} else {
		$tmpplayer = parse_ini_file($lbpconfigdir.'/player.cfg', true);
		if ($tmpplayer === false)  {
			LOGERR('bin/create_config.php: The file player.cfg could not be parsed, the file may be disrupted. Please check/save your Plugin Config or check file "player.cfg" manually!');
			exit(1);
		}
		LOGDEB("bin/create_config.php: Player config has been loaded",7);
	}

	$player = ($tmpplayer['SONOSZONEN']);
	foreach ($player as $zonen => $key) {
		$sonosnet[$zonen] = explode(',', $key[0]);
	} 
	$sonoszonen['sonoszonen'] = $sonosnet;
	
	// finale config für das Script
	$config = array_merge($sonoszonen, $tmpsonos);
	if (file_exists($configfile)) {
		@unlink($configfile);
		file_put_contents($configfile, json_encode($config, JSON_PRETTY_PRINT));
		echo "<INFO> JSON configuration file has been updated".PHP_EOL;
	} else {
		file_put_contents($configfile, json_encode($config, JSON_PRETTY_PRINT));
		echo "<INFO> New JSON configuration file has been created".PHP_EOL;
	}
	if ($call == "true")    {
		#shell_exec('php updateplayer.php');
		$version = LBSystem::pluginversion();
		include('updateplayer.php');
	}
	#print_r($sonoszonen);
	#print_r($tmpsonos);
}
?>