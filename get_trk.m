function get_trk(apt_path, video_path, trx_path, directory)
%Ben Habermeyer
%
%Function launches APT GUI for automatic tracking of a video using a
%pre-trained .lbl file
%
%see
%https://github.com/kristinbranson/APT/wiki/Tracking-Movies-(DL-algorithms)
%for additional help
%
%Inputs
%apt_path: path to apt folder directory
%video_path: path to video ending in filetype, ex directory/video1.mp4
%trx_path: path to .mat file containing flytracker trx
%directory: folder where all project files are located

%debugging
apt_path = 'C:\Users\Ben\Documents\BehaviorClassifier_Master_Folder\APT';
video_path = 'C:\Users\Ben\Documents\COURTSHIP TEST VID\video1.MP4';
trx_path = 'C:\Users\Ben\Documents\COURTSHIP TEST VID\trx.mat';
directory = 'C:\Users\Ben\Documents\COURTSHIP TEST VID';

%adds folder to path
addpath(genpath(apt_path))

%starts APT GUI
lObj = StartAPT;

%load the lbl project in the GUI (MANUAL NOW< MAKE AUTO)

%get the default outfile name of the selected tracker
tmp = lObj.movieFilesAllFull(1);
temp = defaultTrkFileName(lObj,tmp{:});
[~,a,b] = fileparts(temp);
trkname = [a,b];

%call APT tracking from command line
trk_path = [directory, '\', trkname];
lObj.tracker.track({video_path}, 'trkfiles', {trk_path}, 'trxfiles', {trx_path});

end