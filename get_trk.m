function get_trk(apt_path, video_path, trx_path, lbl_path)
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
%lbl_path: path to .lbl file containing pretrained tracker

%debugging
%{
clear
apt_path = 'C:\Users\Ben\Documents\BehaviorClassifier_Master_Folder\APT-master';
video_path = 'C:\Users\Ben\Documents\COURTSHIP TEST VID\video1.MP4';
trx_path = 'C:\Users\Ben\Documents\COURTSHIP TEST VID\trx.mat';
lbl_path = 'C:\Users\Ben\Documents\BehaviorClassifier_Master_Folder\JAB and LBL projects\wing_tracker_v4.lbl';
%}

%adds folder to path
addpath(genpath(apt_path))

%generate filename for trk output
[directory, vid, ~] = fileparts(video_path);
[~,lblname,~] = fileparts(lbl_path);
trk_path = [directory, '\', vid, '_', lblname, '_cpr.trk']; %note assumes cpr tracker

%launch APT and generate trk file
lObj = StartAPT;
APTCluster(lbl_path,'track',video_path,trx_path,'rawtrkname',trk_path);

end