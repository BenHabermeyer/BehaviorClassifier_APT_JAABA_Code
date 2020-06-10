%Program finds how many frames have been repeated at start of video
%tracking by FlyTracker and removes them from the beginning to
%remove the 'lag' from the tracking and scores when uploaded to JAABA for
%better ground truthing. Re computes scores
%
%Directory is a folder containing the video you have tracked and classified
%already. 

%ask the user to select a folder containing the tracked and scored video
folder = uigetdir();
trxfile = strcat(folder, '\', 'trx.mat');
load(trxfile, 'timestamps', 'trx');

%first find a fly where the starting values are not NaN
id = 0;
for fly = 1:length(trx)
    if trx(fly).firstframe == 1
        id = fly;
        break
    end
end

%find the number of repeated frames at the start of the video
xpos = trx(id).x;
startind = 1;
while true
    if xpos(startind) == xpos(startind + 1)
        startind = startind + 1;
    else
        break
    end
end
extraframes = startind - 1;
disp(strcat('number of repeated frames: ', num2str(extraframes)));

%only change everything if the number of extra frames is nonzero
if extraframes > 0
    %fix everything in the trx file based on this number of frames to
    %remove from the beginning
    for fly = 1:length(trx)
        trx(fly).endframe = trx(fly).endframe - extraframes;
        trx(fly).nframes = trx(fly).nframes - extraframes;
        trx(fly).timestamps = trx(fly).timestamps(1:end-extraframes);
        trx(fly).firstframe = trx(fly).nframes - length(trx(fly).timestamps) + 1;
        trx(fly).off = 1 - trx(fly).firstframe;
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
    end
    
    timestamps = timestamps(1:end-extraframes);
    
    %save the new trx to trxfile and scores file
    save(trxfile, 'timestamps', 'trx');
    
    %delete the old scores and perframe files
    delete(strcat(folder, '\scores_LungeV2.mat'));
    delete(strcat(folder, '\perframe\*.mat'));
    
    %re-classify video with the new trx file
    jaaba_path = 'C:\Users\bmain\PycharmProjects\Behavior_Classifier_Ben\JAABA-master\perframe';
    classifier = 'C:\Users\bmain\PycharmProjects\Behavior_Classifier_Ben\LungeV2.jab';
    classify_behavior(jaaba_path, classifier, folder)
end
disp('All done!')
