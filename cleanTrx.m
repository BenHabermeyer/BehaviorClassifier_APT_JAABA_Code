function cleanTrx(trxfile, videofile)
%Function takes in a trx file and removes the first frame of the frameshift
%if there is a difference between video and trx number of frames
%for some reason flytracker likes to pad the video with repeated frames...
%these must be removed prior to classification

%debug
%{
clear
trxfile = 'C:\Users\Ben\Documents\COURTSHIP TEST VID\trx.mat';
videofile = 'C:\Users\Ben\Documents\COURTSHIP TEST VID\video1.MP4';
%}

%inputs are the trx file full path
load(trxfile, 'timestamps', 'trx');

video = VideoReader(videofile);
nframes = video.NumberOfFrames;

%first find a fly where the starting values are not NaN and is longest
id = 0;
for fly = 1:length(trx)
    if trx(fly).firstframe == 1 && length(trx(fly).x) == length(timestamps)
        id = fly;
        break
    end
end

%find the number of repeated frames at the start of the video
xpos = trx(id).x;
ypos = trx(id).y;
startind = 1;
while true
    if xpos(startind) == xpos(startind + 1) && ypos(startind) == ypos(startind + 1)
        startind = startind + 1;
    else
        break
    end
end
extraframes = startind - 1;
disp(strcat('number of repeated frames at start: ', num2str(extraframes)));

%do we need to change the trxfile
makechange = false;

%only change everything if the number of extra frames is nonzero
if extraframes > 0
    makechange = true;
    %fix everything in the trx file based on this number of frames to
    %remove from the beginning   
    timestamps = timestamps(1:end-extraframes);
    
    for fly = 1:length(trx)
        trx(fly).endframe = trx(fly).endframe - extraframes;
        if trx(fly).firstframe == 1
            trx(fly).timestamps = trx(fly).timestamps(1:end-extraframes);
            trx(fly).nframes = trx(fly).nframes - extraframes;
            trx(fly).dt = trx(fly).dt(1:end-extraframes);           
            trx(fly).x = trx(fly).x(startind:end);
            trx(fly).y = trx(fly).y(startind:end);
            trx(fly).theta = trx(fly).theta(startind:end);
            trx(fly).a = trx(fly).a(startind:end);
            trx(fly).b = trx(fly).b(startind:end);
            trx(fly).xwingl = trx(fly).xwingl(startind:end);
            trx(fly).ywingl = trx(fly).ywingl(startind:end);
            trx(fly).xwingr = trx(fly).xwingr(startind:end);
            trx(fly).ywingr = trx(fly).ywingr(startind:end);
            trx(fly).x_mm = trx(fly).x_mm(startind:end);
            trx(fly).y_mm = trx(fly).y_mm(startind:end);
            trx(fly).a_mm = trx(fly).a_mm(startind:end);
            trx(fly).b_mm = trx(fly).b_mm(startind:end);
            trx(fly).theta_mm = trx(fly).theta_mm(startind:end);
        else
            trx(fly).firstframe = trx(fly).firstframe - extraframes;
            trx(fly).off = 1 - trx(fly).firstframe;
            trx(fly).timestamps = trx(fly).timestamps - extraframes*trx(fly).dt(1);
        end
    end
end

%check if there are too many frames in the trxfile
extraframesend = length(timestamps) - nframes;
disp(strcat('number of repeated frames at end: ', num2str(extraframesend)));

if extraframesend > 0
    makechange = true;
    %crop frames at the end
    timestamps = timestamps(1:nframes);
    for fly = 1:length(trx)
        trx(fly).endframe = nframes;
        trx(fly).timestamps = trx(fly).timestamps(1:end-extraframesend);
        trx(fly).nframes = trx(fly).nframes - extraframesend;
        trx(fly).dt = trx(fly).dt(1:end-extraframesend);           
        trx(fly).x = trx(fly).x(1:end-extraframesend);
        trx(fly).y = trx(fly).y(1:end-extraframesend);
        trx(fly).theta = trx(fly).theta(1:end-extraframesend);
        trx(fly).a = trx(fly).a(1:end-extraframesend);
        trx(fly).b = trx(fly).b(1:end-extraframesend);
        trx(fly).xwingl = trx(fly).xwingl(1:end-extraframesend);
        trx(fly).ywingl = trx(fly).ywingl(1:end-extraframesend);
        trx(fly).xwingr = trx(fly).xwingr(1:end-extraframesend);
        trx(fly).ywingr = trx(fly).ywingr(1:end-extraframesend);
        trx(fly).x_mm = trx(fly).x_mm(1:end-extraframesend);
        trx(fly).y_mm = trx(fly).y_mm(1:end-extraframesend);
        trx(fly).a_mm = trx(fly).a_mm(1:end-extraframesend);
        trx(fly).b_mm = trx(fly).b_mm(1:end-extraframesend);
        trx(fly).theta_mm = trx(fly).theta_mm(1:end-extraframesend);
    end
end

%save the new trx to trxfile and scores file
if makechange
    save(trxfile, 'timestamps', 'trx');
end

end

