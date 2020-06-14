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
		#find centers of wells for matching flies to well
		self.find_centers() # PATRICK EXCLUDES THIS
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
		self.well_dictionary : dictionary mapping well to x and y center coordinates
		self.well_circles : list containing lists of x,y, and radii coordinates of well circles
		self.x_centers : x pixel coordinates of well centers
		self.y_centers : y pixel coordinates of well centers
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

	def load_codepath(self):
		"""
		Launch a GUI so people can click on the folder with the code
		"""
		print('Please select the folder containing .m code files')
		root = tk.Tk()
		root.withdraw()
		self.code_path = filedialog.askdirectory() 
		root.destroy()

	def load_flytrackerpath(self):
		"""
		Launch a GUI so people can click on the folder with flytracker
		"""
		print('Please select the folder containing flytracker files')
		root = tk.Tk()
		root.withdraw()
		self.flytracker_path = filedialog.askdirectory() 
		root.destroy()

	def load_jaabapath(self):
		"""
		Launch a GUI so people can click on the folder with JAABA
		"""
		print('Please select the folder containing JAABA')
		root = tk.Tk()
		root.withdraw()
		self.jaaba_path = filedialog.askdirectory()
		root.destroy()

	def load_classifierpath(self):
		"""
		Launch a GUI so people can click on the file with .jab project
		"""
		print('Please select the .jab classifier you would like to use')
		root = tk.Tk()
		root.withdraw()
		self.classifier_path = filedialog.askopenfilename(filetypes=[('jab projects', '*.jab')]) 
		root.destroy()

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

	def load_aptfolder(self):
		"""
		Launch a GUI so people can click on the folder with APT
		"""
		print('Please select the folder containing APT')
		root = tk.Tk()
		root.withdraw()
		self.apt_path = filedialog.askdirectory()
		root.destroy()

	def load_lblfile(self):
		"""
		Launch a GUI so people can click on the file with .lbl project
		"""
		print('Please select the .lbl tracker you would like to use')
		root = tk.Tk()
		root.withdraw()
		self.tracker_path = filedialog.askopenfilename(filetypes=[('lbl projects', '*.lbl')]) 
		root.destroy()

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

	def find_centers(self):
		"""
		Function finds the centers of circular wells for later analysis where flies will be identified by which well they are 
		closest to the center of.
		"""
		#read the pixels per mm from the calibration file to decide how big circles to look for
		matlab_struct = loadmat(self.calib, struct_as_record=False)
		ppm = matlab_struct['calib'][0,0].PPM[0,0]
		#diameter of well is 16mm so radius is half that
		pixels = int(round(ppm * 16 / 2))
		width = 10
		lowR = pixels - width
		highR = pixels + width

		num_wells = 12
		videofile = self.filename

		#open the video
		capture = cv2.VideoCapture(videofile)
		
		#indefinitely read in frames, and when 12 circles are present grab their locations and sizes
		boolean = True
		while(boolean):
			ret, frame = capture.read()

			#convert frame to grayscale, blut it, and loop for circles using HoughCircles algorithm
			if frame is not None:
				gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				blur = cv2.medianBlur(gray, 5)
				circles = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, 1, 20, 
					param1=60, param2=30, minRadius=lowR, maxRadius=highR)

				#convert circles to int type
				if circles is not None:
					circles = np.round(circles[0, :]).astype('int')

					#remove intersecting circles, saving to circles2
					circlelist = circles.tolist()
					circles2 = []

					def intersect(list1, list2):
						#takes as input triplets [x1, y1, r1] and [x2, y2, r2] and finds if they intersect
						distance = math.sqrt((list1[0]-list2[0])**2 + (list1[1]-list2[1])**2)
						return distance <= list1[2]

					#iterate through the circles adding to circles2 if they do not overlap with any other circles
					for circ in circlelist:
						if len(circles2) == 0:
							circles2.append(circ)
						else:
							circle_intersects = False
							for circ2 in circles2:
								if intersect(circ, circ2):
									circle_intersects = True
							if circle_intersects == False:
								circles2.append(circ)

					#finally, make circles to be circles2
					circles3 = np.array(circles2)

					#draw the circles
					color1 = random.randint(50, 255)
					color2 = random.randint(50, 255)
					for index, (x, y, r) in enumerate(circles3):
						cv2.circle(frame, (x, y), r, (color1, 0, color2), 2)
					
					#if you found 12 circles do one of the following, else continue
					if len(circles3) == num_wells:
						#show the image with the circles plotted
						while True:
							cv2.imshow("Frame", frame)
							key = cv2.waitKey(0) & 0xFF

							#if it's not good then go to the next one
							if key == ord('n'):
								break

							#save their locations and an image of the circles
							elif key == ord('y'):
								d = self.get_well_labels(circles3)
								d.pop('well0', None)
								dirname = os.path.dirname(videofile) + '/'
								self.well_dictionary = d
								self.well_circles = circles3
								self.fname = dirname + "well_centers.jpg"
								# write image
								cv2.imwrite(self.fname, frame)
								capture.release()
								cv2.destroyAllWindows()
								boolean = False
								break

		#code to segment the well positions and send to python
		xvals = []
		yvals = []
		for i in range(1, 13):
			data = self.well_dictionary['well' + str(i)]
			datasplit = data.split('_')
			xvals.append(int(datasplit[0]))
			yvals.append(int(datasplit[1]))

		#retains the x and y pixel locations of the center of the circles
		self.x_centers = xvals
		self.y_centers = yvals

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
		trxfile = self.root + '/trx.mat'
		eng.cleanTrx(trxfile, nargout = 0)
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass	

	def launch_apt(self):
		"""
		Launches Animal Parts Tracker (APT) GUI in MATLAB code for tracking of the wings using the algorithm trained by Ben M.
		Python pops up a dialogue with instructions to complete wing tracking in APT before continuing
		Note: would be nice to make this run w/o user input, see https://github.com/kristinbranson/APT/wiki/Tracking-Movies-(DL-algorithms)
		However, it still looks like manually loading the tracking project / algorithm is necessary
		"""
		print('Launching APT GUI')
		os.chdir(self.code_path)
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass	
		eng = matlab.engine.start_matlab() 

		#videoname and trx file needed for tracking
		eng.addpath(eng.genpath(self.apt_path))
		eng.StartAPT()
		videoname = self.root
		trxfile = self.root+'/trx.mat'
		lblfile = self.tracker_path
		#eng.wing_tracking_call(videoname,trxfile) # does not currently use these inputs, they are in the call so future versions can run automatically

		#wait for user input to continue
		root = tk.Tk()
		canvas = tk.Canvas(root, width = 550, height = 150)
		canvas.pack()
		
		def continue_code():
				root.destroy()

		instructions = 'INSTRUCTIONS: \n1. File > Open > wing_tracker_v4.lbl/n2. Add Movie > (pick movie and associated trx file)\n3. (with new movie highlighted) Switch to Movie\n4. Track > Track selection and export results > Export Predictions to Trk File (Current Video) > (use default name) OK'    
		txt = canvas.create_text(275, 60, '-text', instructions)
		button = tk.Button (root, text='Press once wing tracking in APT is finished',command=continue_code,bg='white',fg='black')
		canvas.create_window(275, 130, window=button)
		root.mainloop()

		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass	

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

	def get_classifier_data(self):
		"""
		calls MATLAB function to grab the data from the JAABA output and write to an excel file
		"""
		print('Writing lunge data')
		os.chdir(self.code_path)
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass
		eng = matlab.engine.start_matlab() 
		directory = self.root
		videoname = self.name
		head, tail = os.path.split(self.classifier_path)
		classifiername = tail.split('.')[0]
		excluded = self.excluded_wells
		xvals = self.x_centers
		yvals = self.y_centers

		#call whichever classifier you want
		eng.get_lunges3(directory, videoname, classifiername, excluded, xvals, yvals, nargout = 0)
		try:  # try quiting out of any lingering matlab engines
			eng.quit()
		except:  # if not just keep going with the code
			print('could not find any engines to quit')
			pass

	def get_well_labels(self, array):
		"""
		The purpose of this code is to use the circle generated from detect to generate a label (e.g. well0, well1,
		well2) that associates with it. Well number is left to right, top to the bottom
		:param array: an nx3 array(here 12x3), consisting of the (x,y) origin and radius of a circle.

		IMPORTANT
		---------
		Code Assumes that the number of wells is 12, if not this parameter needs to be changed below
		"""
		num_wells = 12  # Change this parameter as needed
		# Create dictionary for the 12 wells we'll edit later
		d = {'well' + str(i): i for i, j in enumerate(range(num_wells))}
		# inputted array is x,y,r of each circle, grab the x and y
		array = np.array(list(zip(array[:, 0], array[:, 1])))
		
		# let's organize y values first
		n1, n2 = 0, 4  # Slicing start, stop for the array we'll index
		c = 1  # counter for the well label
		while n2 <= num_wells:
			# Create an array of just y values to loop over
			y_arr = np.array([x for i, x in enumerate(array)
						if i in array[:, 1].argsort()[n1:n2]])
			# loop over the array we just made and inside the loop
			# organize each y by the x, then edit value into dict d
			for iterr, indx in enumerate(y_arr[:, 0].argsort()):
				vals = str(y_arr[indx][0]) + '_' + str(y_arr[indx][1])
				# add the values into the d, then increase the counter
				d['well' + str(c)] = vals
				c += 1
			n1 += 4
			n2 += 4
		return d

#create instance of class and run
if __name__ == '__main__':
	s = time.time()
	self = BehaviorClassifier()
	print('Program took this long to run: ' + str(time.time() - s) + ' seconds')

	#if you want to show all the function outputs, uncomment the line below
	self.show_attributes()