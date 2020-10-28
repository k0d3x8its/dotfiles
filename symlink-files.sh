#!/usr/bin/env bash

#####################################
# This script creates symlinks from #
# the home directory to any desired #
# dotfiles in ~/dotfiles            #
####################################

#############
# Variables #
#############

# dotfiles directory
dirDots=~/dotfiles

#old dotfiles - backup directory
oldDirDots=~/dotfiles_old

# list of files/folders to symlink in home directory
files="bashrc fonts vim vimrc"


#########################
# Creating dotfiles_old #
# in the home directory #
#########################
echo "Creating $oldDirDots for backup of any existing dotfiles..."
mkdir -p $oldDirDots
sleep 0.5
echo "...done"
sleep 0.5


######################################
# Changing to the dotfiles directory #
######################################
echo "Changing to the $dirDots directory..."
cd $dirDots
sleep 0.5
echo "...done"
sleep 0.5


#######################################
# Moves any existing dotfiles in the  #
# home directory to dotfiles_old      #
# directory. It then creates symlinks #
#######################################
for file in $files 
	do
		if [ -f ~/.$file ];
		then
			echo "Moving previous version of $file from ~ to $oldDirDots..."
			sleep 0.5
			mv ~/.$file $oldDirDots
			echo "...done"
		fi

		echo "Creating symlink to $file in home directory..."
		sleep 0.5
		ln -s $dirDots/$file ~/.$file
		echo "...done"
	done
