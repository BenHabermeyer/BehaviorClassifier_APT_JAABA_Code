%{
This file is for running after BehaviorClassifier.py to fix problems with
Flytracker's Offset, which produces a lag in the tracking and behavior when
aligned with a video on JAABA.

Use: Select a folder containing the .trx file you would like to modify.
Then select whether you would like to add frames - fly moves before trx, or
remove frames - fly moves before trx

Note: code assumes classifier is LungeV3.jab so let Ben know if this is not
the case.
%}

%ask the user to select a folder containing the tracked and scored video
folder = uigetdir();
trxfile = strcat(folder, '\', 'trx.mat');
load(trxfile, 'timestamps', 'trx');

%ask the user what type of offset they would like to do
answer1 = questdlg('How would you like to offset the trx file? Remove frames - fly moves before trx, or add frames - trx moves before fly.', ...
	'Input 1', ...
	'Remove frames','Add frames','Remove frames');

%ask the user for the number of frames to change
prompt = {'Enter number of frames to offset the trx file by:'};
dlgtitle = 'Input 2';
dims = [1 50];
answer2 = inputdlg(prompt,dlgtitle,dims);
offset = str2double(answer2{1});

switch answer1
    case 'Remove frames'
        extraframes = offset;
        startind = extraframes + 1;
        %fix everything in the trx file based on this number of frames to
        %remove from the beginning
        timestamps = timestamps(1:end-extraframes);    
        for fly = 1:length(trx)
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
            trx(fly).endframe = trx(fly).endframe - extraframes;
        end
    case 'Add frames'
        % append extra timestamps to the end
        for i = 1:offset
            timestamps = horzcat(timestamps, timestamps(end)+1/30);
        end
        for fly = 1:length(trx)
            if trx(fly).firstframe == 1
                trx(fly).nframes = trx(fly).nframes + offset;
                trx(fly).timestamps = timestamps;
                trx(fly).dt = horzcat(trx(fly).dt, repmat(1/30, 1, offset));
                trx(fly).x = vertcat(repmat(trx(fly).x(1), offset, 1), ...
                    trx(fly).x);
                trx(fly).y = vertcat(repmat(trx(fly).y(1), offset, 1), ...
                    trx(fly).y);
                trx(fly).theta = vertcat(repmat(trx(fly).theta(1), offset, 1), ...
                    trx(fly).theta);
                trx(fly).a = vertcat(repmat(trx(fly).a(1), offset, 1), ...
                    trx(fly).a);
                trx(fly).b = vertcat(repmat(trx(fly).b(1), offset, 1), ...
                    trx(fly).b);
                trx(fly).xwingl = vertcat(repmat(trx(fly).xwingl(1), offset, 1), ...
                    trx(fly).xwingl);
                trx(fly).ywingl = vertcat(repmat(trx(fly).ywingl(1), offset, 1), ...
                    trx(fly).ywingl);
                trx(fly).xwingr = vertcat(repmat(trx(fly).xwingr(1), offset, 1), ...
                    trx(fly).xwingr);
                trx(fly).ywingr = vertcat(repmat(trx(fly).ywingr(1), offset, 1), ...
                    trx(fly).ywingr);
                trx(fly).x_mm = vertcat(repmat(trx(fly).x_mm(1), offset, 1), ...
                    trx(fly).x_mm);
                trx(fly).y_mm = vertcat(repmat(trx(fly).y_mm(1), offset, 1), ...
                    trx(fly).y_mm);
                trx(fly).a_mm = vertcat(repmat(trx(fly).a_mm(1), offset, 1), ...
                    trx(fly).a_mm);
                trx(fly).b_mm = vertcat(repmat(trx(fly).b_mm(1), offset, 1), ...
                    trx(fly).b_mm);
                trx(fly).theta_mm = vertcat(repmat(trx(fly).theta_mm(1), offset, 1), ...
                    trx(fly).theta_mm);
            else
                trx(fly).firstframe = trx(fly).firstframe + offset;
                trx(fly).off = trx(fly).off - offset;
                trx(fly).timestamps = timestamps(trx(fly).firstframe:end);
                trx(fly).dt = horzcat(trx(fly).dt, repmat(1/30, 1, offset));
                trx(fly).dt = trx(fly).dt(1+offset:end);
            end       
            trx(fly).endframe = trx(fly).endframe + offset;
        end
end
    
%save the new trx to trxfile and scores file
save(trxfile, 'timestamps', 'trx');

%delete the old scores and perframe files
delete(strcat(folder, '\scores_LungeV3.mat'));
delete(strcat(folder, '\perframe\*.mat'));

%re-classify video with the new trx file
jaaba_path = 'C:\Users\bmain\PycharmProjects\Behavior_Classifier_Ben\JAABA-master\perframe';
classifier = 'C:\Users\bmain\PycharmProjects\Behavior_Classifier_Ben\LungeV3.jab';
classify_behavior(jaaba_path, classifier, folder)
disp('All done!')
