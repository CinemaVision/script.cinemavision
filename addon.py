#=================================================================================
#
#       File: addon.py
#       Function: 
#       Author(s): Ragnarok
#
#
#       Kodi CinemaVision Script                        Revised: 02/26/2015
#       Copyright© 2015 CinemaVision                    www.cinemavision.org
#
#=================================================================================

#==================================================
#
#                    SETTINGS
#
# TAB: Videos
#	ITEM: Enable Rating Video(s)
#		TYPE: True/False
#		FUNCTION: Enable rating video(s).
#	ITEM: Enable Audio Format Video(s)
#		TYPE: True/False
#		FUNCTION: Enable audio format video(s).

#	ITEM: Intermission Video(s)
#		TYPE: Dropdown/Value
#		FUNCTION: Set the intermission video(s).
#		VALUES: Single Video/Playlist | 1-5 Random Videos

# TAB: Trivia
# TAB: Trailers
#	ITEM: Trailer(s)
#		TYPE: Dropdown/Value
#		FUNCTION: Set the number of trailers to play before the feature.
#		VALUES: 1 Trailer | 2 Trailers | 3 Trailers | 4 Trailers | 5 Trailers | 10 Trailers
#	ITEM: Trailer Scraper
#		TYPE: Dropdown/Value
#		FUNCTION: Set the scraper to use for trailers.
#		VALUES: Populated from video plugins. Auto fill and require Apple Movie Trailers (newest).

# TAB: Feature Presentation
#	ITEM: Display Queue Instructions
#		TYPE: True/False
#		FUNCTION: Show or hide queue instructions for the script.
#	ITEM: Number of Features
#		TYPE: Dropdown/Value
#		FUNCTION: Set the number of possible features
#		VALUES: 1-5 Features

#
# TAB: Home Automation
#	ITEM: 
#		TYPE: 
#		FUNCTION: 
#		VALUES: 
#
# TAB: Miscellaneous
#	ITEM: Override Play Button (Experiemental)
#	TYPE: True/False
#		FUNCTION: Force CinemaVision script to run whenever a movie is played.
#	ITEM: Enable Output to VoxCommando
#	TYPE: True/False
#		FUNCTION: Enable output to VoxCommando from script.
#	ITEM: Create Directory Tree
#		FUNCTION: Create the required directory tree in the specified folder.
#
#
#	ITEM: 
#	TYPE: True/False
#		FUNCTION: 
#==================================================

#==================================================
#
#                    FEATURES
#
# Create settings layout & links
# Create basic folder structure in a specified directory
# Intro/outro video support
# Trivia slides & trivia video support
#
# Music during pre-show from folder or playlist
# Home automation script support
#	- resources/automation
#
#==================================================

# Import Python Modules
import os

# Import Kodi Modules
import xbmcgui, xbmc, xbmcaddon, xbmcvfs

# Import Custom Modules

# Define Script Information Variables
__addon__                = xbmcaddon.Addon('script.cinemavision')
__scriptID__             = __addon__.getAddonInfo('id')
__script__               = __addon__.getAddonInfo('name')
__version__              = __addon__.getAddonInfo('version')
__addonname__            = __script__

