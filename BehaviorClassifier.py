import numpy as np
import tkinter as tk
from tkinter import Tk, filedialog, messagebox
from tkinter import*
import os, subprocess, cv2, pickle
from multiprocessing import Pool
import moviepy.editor as mpy
from moviepy.editor import*
from moviepy.config import get_setting
import time, moviepy, matlab.engine, shutil, math
from scipy.io import loadmat
import random
from PIL import Image, ImageTk, ImageDraw
import PIL
import time
import logging

class BehaviorClassifier(object):
	'''
	This is the main analysis file for tracking Drosophila videos and applying behavior classifiers created
	in JAABA. Execution of this code allows a user to select one video to analyze, and apply the classifier
	that they choose. Simply execute in a terminal BehaviorClassifier.py to use and follow the steps when
	prompted.

	Notes: Code assumes number of wells does not exceed 12.

	Authors: Ben Habermeyer, Logan and Patrick McClanahan
	Contact: benhabe@seas.upenn.edu, 434-242-6984
	'''

	def __init__(self):
		'''
		Initializes path variables to the code, classifier, tracker, and jaaba, and executes the functions
		to select and classify a video
		'''

		#select the video file
		self.load_single()

		#set up the logger file in the video directory
		self.setup_logger()

		try:
			#select all other folders and files needed
			self.load_codepath()
			self.load_flytrackerpath()
			self.load_jaabapath()
			self.load_classifierpath()
			self.load_aptpath()

			#ask if you want to crop the first x seconds
			self.ask_crop()

			#MATLAB stuff
			#calibrate the tracker NOT SURE IF THIS IS THE BEST WAY TO DO THIS RN MIGHT ADD STEPS LATER
			self.ask_calibrate() 
			#wells to exclude
			self.checkbox_grid()
			#track the video
			self.run_tracker()
			#reorganize the folders for JAABA
			self.prepare_JAABA()
			#launch APT GUI, if requested
			if self.req_apt:
				self.launch_apt()
			
			#JAABA stuff
			#run the JAABA program
			self.classify_behavior()
			#get the output data file
			self.get_classifier_data()

			#if you want to show all the function outputs, uncomment the line below
			self.show_attributes()
			print('*****************************************************')
			print('COMPLETED')
			print('*****************************************************')
		except Exception:
			self.show_attributes()
			print('*****************************************************')
			print('ERROR - CHECK LOG FILE')
			print('*****************************************************')
			self.logger.error("Fatal error in main loop", exc_info=True)

		'''
		VARIABLES CREATED
		self.code_path : path to where the code is kept
		self.classifier_path : path to .jab file
		self.flytracker_path : FlyTracker folder path on computer
		self.jaaba_path : JAABA folder path on computer
		self.apt_path : APT folder path on computer
		self.tracker_path : path to .lbl file
		self.req_apt : boolean whether APT file was added or not
		self.filename : full path to and ending with video name 
		self.root : root of folder containing video, filename without the file extension
		self.name : video name without extension
		self.fullname : the video name with extension
		self.calib : path to the calibration .mat file
		self.excluded_wells : list of wells to remove from analysis
		self.trxfile : path to trx.mat file
		self.logger : logger which adds messages to .log file
		'''

	def load_single(self):
		"""
		Launch a GUI so people can click on the videofile that they want to track
		"""
		print('Please select the file corresponding to the video you would like to process')
		root = tk.Tk()
		root.withdraw()
		self.filename = filedialog.askopenfilename(filetypes=[('mp4', '*mp4'), ('MP4', '*MP4')])  # Set the filename of the video
		self.root = self.parent(self.filename)  # Set the video's folder
		self.name, self.fullname = self.get_fname(self.filename)
		root.destroy()

	def setup_logger(self):
		self.logger = logging.getLogger(__name__)
		self.logger.setLevel(logging.INFO)
		file_handler = logging.FileHandler(os.path.join(self.root, 'BehaviorClassifier.log'))
		formatter = logging.Formatter('%(levelname)s:%(funcName)s:%(message)s')
		file_handler.setFormatter(formatter)
		self.logger.addHandler(file_handler)
		
		self.logger.info('Logger Instantiated')
		self.logger.info('Video Selected')

	def load_codepath(self):
		"""
		Launch a GUI so people can click on the folder with the code
		"""
		print('Please select the folder containing .m code files')
		root = tk.Tk()
		root.withdraw()
		self.code_path = filedialog.askdirectory() 
		root.destroy()
		self.logger.info('Code Path Selected')

	def load_flytrackerpath(self):
		"""
		Launch a GUI so people can click on the folder with flytracker
		"""
		print('Please select the folder containing flytracker files')
		root = tk.Tk()
		root.withdraw()
		self.flytracker_path = filedialog.askdirectory() 
		root.destroy()
		self.logger.info('FlyTracker Path Selected')

	def load_jaabapath(self):
		"""
		Launch a GUI so people can click on the folder with JAABA
		"""
		print('Please select the folder containing JAABA')
		root = tk.Tk()
		root.withdraw()
		self.jaaba_path = filedialog.askdirectory()
		root.destroy()
		self.logger.info('JAABA Path Selected')

	def load_classifierpath(self):
		"""
		Launch a GUI so people can click on the file with .jab project
		"""
		print('Please select the .jab classifier you would like to use')
		root = tk.Tk()
		root.withdraw()
		self.classifier_path = filedialog.askopenfilename(filetypes=[('jab projects', '*.jab')]) 
		root.destroy()
		self.logger.info('Classifier .jab File Selected')

	def load_aptpath(self):
		"""
		Launch a GUI to ask if person wants to add APT tracker
		"""
		root = tk.Tk()
		root.withdraw()
		MsgBox = tk.messagebox.askquestion('Add APT',"Would you like to add an APT tracker before classification?", icon = 'warning')
		if MsgBox == 'yes':
			root.destroy()
			self.load_aptfolder()
			self.load_lblfile()
			self.req_apt = True
		else:
			root.destroy()
			self.req_apt = False
			self.logger.info('APT Path NOT Selected')

	def load_aptfolder(self):
		"""
		Launch a GUI so people can click on the folder with APT
		"""
		print('Please select the folder containing APT')
		root = tk.Tk()
		root.withdraw()
		self.apt_path = filedialog.askdirectory()
		root.destroy()
		self.logger.info('APT Path Selected')

	def load_lblfile(self):
		"""
		Launch a GUI so people can click on the file with .lbl project
		"""
		print('Please select the .lbl tracker you would like to use')
		root = tk.Tk()
		root.withdraw()
		self.tracker_path = filedialog.askopenfilename(filetypes=[('lbl projects', '*.lbl')]) 
		root.destroy()
		self.logger.info('Tracker .lbl File Selected')

	def parent(self, path):
		"""Returns parent directory of a path"""
		return os.path.dirname(path)

	def get_fname(self, fullpath):
		"""Returns the base name of the path without filetype and with filetype
		e.x.
		input: '/Users/DrSwag/EverydayIm/Hustling.mp4'
		output: 'Hustling', 'Hustling.mp4'
		"""
		return os.path.basename(fullpath)[:-4], os.path.basename(fullpath)

	def show_attributes(self):
		"""
		Code serves to update attributes that are attached to the class, e.g. filetype/filename, and
		prints them all out to the user.
		"""
		self.attributes = '\n'.join("%s: %s" % item for item in vars(self).items())
		print('\nHere are the attributes you can access using .:')
		print(self.attributes)
		self.logger.info('Here are the attributes you can access using .:')
		self.logger.info(self.attributes)

	def ask_crop(self):
		"""
		Asks if you would like to crop the start of a video to fix the aperture settings. If no does nothing.
		if yes then calls next dialog asking how long
		"""
		root = tk.Tk()
		root.withdraw()
		MsgBox = tk.messagebox.askquestion('Crop Video',"Would you like to crop the video?", icon = 'warning')
		if MsgBox == 'yes':
			root.destroy()
			self.how_long_crop()
		else:
			root.destroy()
			self.logger.info('Cropping NOT Selected')

	def how_long_crop(self):
		"""
		Another dialog asking how many seconds you would like to crop off the start of the video. Enter the number of
		seconds cropped
		"""
		#callback function for the tkinter entries
		def get_time():
			#get the start and end times and save as variable
			self.crop_time1 = int(Entry.get(entry_1))
			self.crop_time2 = int(Entry.get(entry_2))
			my_window.withdraw()
			self.crop_start()
			my_window.destroy()

		#master window
		my_window = Tk()

		#create labels and entry space for text
		label_1 = Label(my_window, text = 'How many seconds would you like to crop from the start:')
		entry_1 = Entry(my_window)

		#create second label for length of video
		label_2 = Label(my_window, text = 'When would you like the cropped video to end in seconds:')
		entry_2 = Entry(my_window)

		label_1.grid(row = 0, column = 0)
		entry_1.grid(row = 0, column = 1)

		label_2.grid(row = 1, column = 0)
		entry_2.grid(row = 1, column = 1)

		#add a "done" button to press when finished
		button_1 = Button(my_window, text = "Done", command = get_time)
		button_1.grid(row = 2, column = 0)

		#run indefinitely
		my_window.mainloop()

	def crop_start(self):
		"""
		Crops the beginning of a video based on the self.crop_time defined in the how_long_crop function.
		Updates the filename, name, and fullname to be that of the newly cropped video and moves the original
		video to a new folder so it does not also get tracked.
		"""
		print('Starting video crop')
		p = Pool(2)
		#need to set current directory for moviepy
		os.chdir(self.root)
		path = self.filename
		start_time = self.crop_time1
		end_time = self.crop_time2

		#rename the cropped file
		filetype = self.fullname.split('.')[-1]
		outputname = self.name + '_cropped.' + filetype

		#use moviepy to extract the desired subclip
		oldvideo = VideoFileClip(self.fullname)
		clipped = oldvideo.subclip(start_time, end_time)
		clipped.write_videofile(outputname, codec = 'libx264')
		oldvideo.close()

		#create a new subfolder to put the original video in - FlyTracker tracks all videos in folder
		newfolder = self.root + '/' + 'uncropped_video'
		os.mkdir(newfolder)
		shutil.move(self.fullname, newfolder)

		#rename the originial file and path to be the new cropped file
		self.fullname = outputname
		self.name = self.name + '_cropped'
		self.filename = self.root + '/' + self.fullname
		self.logger.info('Cropping Completed')

	def ask_calibrate(self):
		"""
		Asks if you would like to call flytracker calibration, if yes launches, if no select the calib file
		"""
		root = tk.Tk()
		root.withdraw()
		MsgBox = tk.messagebox.askquestion('Crop Video',"Would you like to launch FlyTracker calibration?", icon = 'warning')
		if MsgBox == 'yes':
			root.destroy()
			self.calibrate_tracker()
		else:
			root.destroy()
			self.select_calib()

	def select_calib(self):
		"""
		select the calibration .mat file from a pre-calibrated video - remember which wells are excluded
		"""
		print('Please select the calibration .mat file corresponding to the video')
		root = tk.Tk()
		root.withdraw()
		self.calib = filedialog.askopenfilename(filetypes=[('Calibration file', '*_calibration.mat')]) 
		root.destroy()
		self.logger.info('Calibration File Selected')

	def calibrate_tracker(self):
		"""
		Launches MATLAB code for automatic calibration of the video. Follow steps outlined on FlyTracker
		website for tracking, manually-excluding wells you do not want to analyze
		"""
		os.chdir(self.code_path)
		print('Launching FlyTracker Calibration')
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass
		eng = matlab.engine.start_matlab() 

		# for each of the videos, launch AutoCalibrate.m matlab script
		# takes as input the path to the video and the path to the calibration file
		video = self.filename # this is the file to the trimmed video per well
		self.calib = video.split('.')[0] + '_calibration.mat' 
		# Launch FlyTracker Calibration - takes as input the path name to the video and flytracker and calibration file
		eng.auto_calibrate(self.flytracker_path, video, self.calib, nargout = 0) 

		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass

		#calls dialog to ask if calibration should be accepted
		self.good_calibration()
		self.logger.info('FlyTracker Calibration Completed')
		
	def good_calibration(self):
		"""
		Dialog asks thse user if he/she was pleased with the calibration. If not, calibration files
		are deleted and the calibration is called again.
		"""
		#create a tkinter window
		root = tk.Tk()
		#hide the master window to prompt a question window
		root.withdraw()
		#ask the question in a messagebox
		MsgBox = tk.messagebox.askquestion('Accept Calibration',"Would you like to accept the calibration?", icon = 'warning')
		if MsgBox == 'yes':
			root.destroy()
		elif MsgBox == 'no':
			#deletes old calibration files and calls calibrator again
			calib_folder = self.root + '/' + self.name
			shutil.rmtree(calib_folder)
			calib_file = self.root + '/' + self.name + '_calibration.mat'
			os.unlink(calib_file)
			root.destroy()
			self.calibrate_tracker()

	def checkbox_grid(self):
		"""
		Dialog box with 12 checkboxes for the user to select which wells they would like to exclude, if any. 
		"""
		#list of excluded wells
		print("Launching Well Exclusion Checkbox Grid")
		self.excluded_wells = []

		#callback for the "done" button appends to list wells whose buttons have been pressed
		def get_state():
			var_list = [var1.get(), var2.get(), var3.get(), var4.get(), var5.get(), var6.get(),
			var7.get(), var8.get(), var9.get(), var10.get(), var11.get(), var12.get()]
			self.excluded_wells = [v for v in var_list if v > 0]
			master.destroy()

		#master tkinter window
		master = Tk()

		#load first frame (NB: ImageTk MUST BE CALLED AFTER Tk())
		clip = VideoFileClip(self.filename)
		img = clip.get_frame(0) # load frame
		im_height = np.size(img,1)
		im_width = np.size(img,0)
		PILimg = PIL.Image.fromarray(img) # imagetk needs a PIL image
		PILimg_resize = PILimg.resize((int(im_height/2), int(im_width/2)), PIL.Image.ANTIALIAS)
		ph = ImageTk.PhotoImage(PILimg_resize) # tk needs a photo image

		#grid of checkbuttons corresponding to each well with a value equal to their well number
		#assumes grid of 12 wells
		Label(master, image = ph, bg = "black").grid(row=0, columnspan = 4,  pady = 4)
		Label(master, text="Check Wells to Exclude from Analysis (if any) and click 'Done'").grid(row=1, columnspan = 4,  pady = 4)
		var1 = IntVar()
		Checkbutton(master, text="Well 1", variable=var1, onvalue=1, offvalue=0, anchor='w').grid(row=2, column=0, pady = 4, padx = 8)
		var2 = IntVar()
		Checkbutton(master, text="Well 2", variable=var2, onvalue=2, offvalue=0, anchor='w').grid(row=2, column=1, pady = 4, padx = 8)
		var3 = IntVar()
		Checkbutton(master, text="Well 3", variable=var3, onvalue=3, offvalue=0, anchor='w').grid(row=2, column=2, pady = 4, padx = 8)
		var4 = IntVar()
		Checkbutton(master, text="Well 4", variable=var4, onvalue=4, offvalue=0, anchor='w').grid(row=2, column=3, pady = 4, padx = 8)
		var5 = IntVar()
		Checkbutton(master, text="Well 5", variable=var5, onvalue=5, offvalue=0, anchor='w').grid(row=3, column=0, pady = 4, padx = 8)
		var6 = IntVar()
		Checkbutton(master, text="Well 6", variable=var6, onvalue=6, offvalue=0, anchor='w').grid(row=3, column=1, pady = 4, padx = 8)
		var7 = IntVar()
		Checkbutton(master, text="Well 7", variable=var7, onvalue=7, offvalue=0, anchor='w').grid(row=3, column=2, pady = 4, padx = 8)
		var8 = IntVar()
		Checkbutton(master, text="Well 8", variable=var8, onvalue=8, offvalue=0, anchor='w').grid(row=3, column=3, pady = 4, padx = 8)
		var9 = IntVar()
		Checkbutton(master, text="Well 9", variable=var9, onvalue=9, offvalue=0, anchor='w').grid(row=4, column=0, pady = 4, padx = 8)
		var10 = IntVar()
		Checkbutton(master, text="Well 10", variable=var10, onvalue=10, offvalue=0, anchor='w').grid(row=4, column=1, pady = 4, padx = 8)
		var11 = IntVar()
		Checkbutton(master, text="Well 11", variable=var11, onvalue=11, offvalue=0, anchor='w').grid(row=4, column=2, pady = 4, padx = 8)
		var12 = IntVar()
		Checkbutton(master, text="Well 12", variable=var12, onvalue=12, offvalue=0, anchor='w').grid(row=4, column=3, pady = 4, padx = 8)
		Button(master, text='Done', command=get_state).grid(row=5, column = 1)

		#run loop indefinitely
		master.mainloop()
		self.logger.info('Excluded Wells Completed')

	def run_tracker(self):
		"""
		Launches MATLAB code for automatic tracking of the video after calibration using FlyTracker
		Note: FlyTracker will track every video in directory
		"""
		print('Launching FlyTracker Tracking')
		os.chdir(self.code_path)
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass

		eng = matlab.engine.start_matlab()
		#videoname and calibration file needed for tracking
		foldername = self.root
		extension = '*.' + self.fullname.split('.')[-1]
		#calibration = self.calib
		calibration = self.filename.split('.')[0] + '_calibration.mat'
		eng.auto_track(self.flytracker_path, foldername, extension, calibration, nargout = 0)

		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass
		self.logger.info('FlyTracker Tracking Completed')

	def prepare_JAABA(self):
		"""
		Function prepares the data for JAABA by making the correct directory structure JAABA wants.
		Needs to grab the perframe folder and the tracking file and move to directory for JAABA.
		"""
		print('Preparing files for JAABA')
		
		destination = self.root
		filename = self.name
		trx_path = destination + '/' + filename + '/' + filename + '_JAABA' + '/trx.mat'
		perframe_path = destination + '/' + filename + '/' + filename + '_JAABA/perframe'
		shutil.move(trx_path, destination)
		shutil.move(perframe_path, destination)
		
		#remove any repeated frames
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass
		eng = matlab.engine.start_matlab() 
		self.trxfile = self.root + '/trx.mat'
		eng.cleanTrx(self.trxfile, self.filename, nargout = 0)
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass	
		self.logger.info('Prepared JAABA Files')

	def launch_apt(self):
		"""
		Launches Animal Parts Tracker (APT) in MATLAB code for tracking of the wings using the algorithm trained by Ben M.
		names outfile name of .lbl file with additional _cpr.trk
		"""
		print('Launching APT')
		os.chdir(self.code_path)
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass	
		eng = matlab.engine.start_matlab() 

		#call apt tracking
		eng.get_trk(self.apt_path, self.filename, self.trxfile, self.tracker_path, nargout = 0)

		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass
		self.logger.info('APT Tracking Completed, .trk Created')	

	def classify_behavior(self):
		"""
		Calls JAABA classifier from MATLAB
		.jab file name is stored at the start
		"""
		print('Classifying behavior using JAABA')
		os.chdir(self.code_path)
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass
		eng = matlab.engine.start_matlab() 
		eng.classify_behavior(os.path.join(self.jaaba_path, 'perframe'), self.classifier_path, self.root, nargout = 0)

		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass	
		self.logger.info('JAABA Classification with .jab Completed')

	def get_classifier_data(self):
		"""
		calls MATLAB function to grab the data from the JAABA output and write to an excel file
		"""
		print('Writing classification data')
		os.chdir(self.code_path)
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass
		eng = matlab.engine.start_matlab() 
		directory = self.root
		videoname = self.name
		calibfile = self.calib
		head, tail = os.path.split(self.classifier_path)
		classifiername = tail.split('.')[0]
		excluded = self.excluded_wells

		#creates excel file from data, matches flies to wells
		eng.get_scores_data(directory, videoname, calibfile, classifiername, excluded, nargout = 0)
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass
		self.logger.info('Writing Classification Data to Excel Completed')

#create instance of class and run
if __name__ == '__main__':
	s = time.time()
	self = BehaviorClassifier()
	print('Program took this long to run: ' + str(time.time() - s) + ' seconds')