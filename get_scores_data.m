function get_scores_data(directory, videoname, calibfile, classifiername, excluded) 
  %Ben Habermeyer
    %function takes as input a string containing the name of the directory,
    %a string containing the video name, and a string containing the
    %calibration file, a string containing the clasifier name, and a list 
    %of wells to be excluded
    %
    %finds the initial a and b locations from calibration ROIs
    %outputs an excel file containing the number of bouts and their frame
    %start/end frames for each fly
    %
    %NOTE: pretty hard coded to 12 wells with 24 flies total so will change
    %file if anything different is run
    
    
    % debugging paths
    %{
    clear
    directory = 'C:\Users\Ben\Documents\COURTSHIP TEST VID';
    videoname = 'video1';
    calibfile = 'C:\Users\Ben\Documents\COURTSHIP TEST VID\video1_calibration.mat';
    classifiername = 'LungeV3';
    excluded = [3, 4, 5, 7, 8, 12];
    %}
    
    %add the input folder to path
    addpath(directory);
    addpath(strcat(directory, '\perframe'));

    %PDM load the well centers
    load(calibfile, 'calib')
    
    %load the scored data
    classifier_scores = strcat('scores_', classifiername);
    load(classifier_scores, 'allScores');
    scores = allScores.scores;
    
    %thow an error if number of wells != number of flies
    if length(scores) ~= calib.n_chambers*calib.n_flies
        error("Number of chambers is does not match number of flies, check exclusion")
    end

    %load in the x and y data
    load x.mat
    xdata = data;
    load y.mat
    ydata = data;
    load x_mm.mat
    xmm = data;
    load y_mm.mat
    ymm = data;
    clear data
    
    %get the dimensions of the matrix
    vidsize = size(calib.mask);
    ysize = vidsize(1);
    xsize = vidsize(2);
    
    %construct grid of 12 mock points in this image ~centroids
    %this assumes 3 rows 4 columns
    xaxis = linspace(1, xsize, 6);
    yaxis = linspace(1, ysize, 5);
    [X, Y] = meshgrid(xaxis(2:end-1), yaxis(2:end-1));
    
    %x, y coordinates of meshgrid centroids
    centroids = zeros(2,12);
    counter1 = 1;
    for row = 1:3
        for col = 1:4
            centroids(1, counter1) = X(row, col);
            centroids(2, counter1) = Y(row, col);
            counter1 = counter1 + 1;
        end
    end
    
    %boolean matrix for wells 1-12 whether they are excluded 1 or not 0
    is_excluded = zeros(1,12);
    for i = 1:length(excluded)
        is_excluded(double(excluded{i})) = 1;
    end
    
    %remove excluded centroids - x, y, well number
    nonexcluded_centroids = [];
    for i = 1:12
        if ~is_excluded(i)
            nonexcluded_centroids(end+1, :) = [centroids(1,i), centroids(2,i), i];
        end
    end
    
    %there will be 1-12 well centers depending on how many were excluded
    %NOTE: calib.centroids is not these centroids... use ROI
    xcenters = zeros(1, length(calib.rois));
    ycenters = zeros(1, length(calib.rois));
    for i = 1:length(calib.rois)
        xcenters(i) = calib.rois{i}(2) + (calib.w/2);
        ycenters(i) = calib.rois{i}(1) + (calib.h/2);
    end
    
    %greedily compute which centroid is closest to which and output
    %centroid x, centroid y, well id
    centroids_labeled = [];
    while ~isempty(nonexcluded_centroids)
        %compute distance to each grid centroid, output minumum
        mindist = 100000;
        min_calib_index = 0;
        min_grid_index = 0;
        for i = 1:size(nonexcluded_centroids, 1)
            for j = 1:length(xcenters)
                dist = sqrt((xcenters(j)-nonexcluded_centroids(i,1)).^2 + (ycenters(j)-nonexcluded_centroids(i,2)).^2);
                if dist < mindist
                    mindist = dist;
                    min_calib_index = j;
                    min_grid_index = i;
                end
            end
        end
        centroids_labeled(end+1,:) = [xcenters(min_calib_index), ycenters(min_calib_index), nonexcluded_centroids(min_grid_index,3)];
        nonexcluded_centroids(min_grid_index, :) = [];
        xcenters(min_calib_index) = [];
        ycenters(min_calib_index) = [];
    end
    
    %compute euclidian distance for each of the flies - still unordered
    distance = zeros(1, length(xmm));
    for fly = 1:length(xmm)
        %if one of the values is NaN just call it 0 distance moved
        for tstep = 2:length(xmm{1,fly})
            if (isnan(xmm{1,fly}(tstep-1))) || (isnan(xmm{1,fly}(tstep)))
                distance(fly) = distance(fly);
            else
            distance(fly) = distance(fly) + ...
                sqrt((xmm{1,fly}(tstep-1) - xmm{1,fly}(tstep))^2 + ...
                (ymm{1,fly}(tstep-1) - ymm{1,fly}(tstep))^2);
            end
        end
    end

    %use a cell arary to store wells 1-12 flies A-B and their corresponding
    %information
    ids = cell(24, 8);
    %instantiate positions
    counter = 1;
    for i = 1:12
        for j = 1:2
            if j == 1
                letter = 'A';
            else
                letter = 'B';
            end
            ids{counter, 1} = strcat(num2str(i), letter);
            counter = counter + 1;
        end
    end
    %write to the excluded column
    for i = 1:12
        if is_excluded(i)
            ids{2*i,3} = 'Excluded';
            ids{2*i-1,3} = 'Excluded';
        else
            ids{2*i,3} = '';
            ids{2*i-1,3} = '';
        end
    end
    
    %data of x and y positions, NaN for excluded wells
    %column 1 is x, 2 is y, 3 is JAABA fly #
    positions = NaN(length(scores),3);
    
    for i = 1:length(scores)
        positions(i, 1) = xdata{1, i}(1);
        positions(i, 2) = ydata{1, i}(1);
        positions(i, 3) = i;
    end
    
    %iterate through the positions, assigning which is closest to each well
    wells = NaN(1,length(scores));
    for i = 1:length(scores)
        %use the distance formula to calculate the closest well
        xdiff = (centroids_labeled(:,1) - positions(i,1)).^2;
        ydiff = (centroids_labeled(:,2) - positions(i,2)).^2;
        distances = sqrt(xdiff + ydiff);
        [~, ind] = min(distances);
        wells(i) = centroids_labeled(ind, 3);
    end
    
    %for each well, classify which fly should be A and which should be B
    %use which fly was HIGHER is A - the lower y value of the pair and
    %assign to column 2 of the ids. PDM - if there is only one fly in the
    %well, it defaults to be A.
    for i = 1:12
        if ~is_excluded(i)
            [~, inds] = find(wells == i);
            if length(inds) == 2
            if positions(inds(1),2) < positions(inds(2),2)
                ids{2*i-1,2} = num2str(inds(1));
                ids{2*i,2} = num2str(inds(2));
            else
                ids{2*i-1,2} = num2str(inds(2));
                ids{2*i,2} = num2str(inds(1));
            end
            elseif length(inds) == 1
                ids{2*i-1,2} = num2str(inds(1));
            else
                error('expected 1 or 2 flies per well')
            end
        else
            ids{2*i-1,2} = '';
            ids{2*i,2} = '';
        end
    end

    %load in the postprocessed scores, start time and end time for bouts
    postprocessed = allScores.postprocessed;
    %note: since it is 0 or 1 you really don't need this at all, just start
    %and end times
    
    tstart = allScores.t0s;
    tend = allScores.t1s;
    
    %I  made ids a cell so make a matrix for easy indexing
    ids_mat = NaN(24,1);
    for i = 1:24
        ids_mat(i) = str2double(ids{i, 2});
    end
    
    %loop through all of the wells - ignore if was excluded, otherwise
    %match id to fly and update accordingly
    i = 1;
    for j = 1:24
        if ~isnan(ids_mat(j))
            %just use the information we have from start and end frames
            startframes = tstart{i};
            endframes = tend{i};
            
            %add startframes and endframes to cell array of ids
            ids_ind = find(ids_mat == i);
            starttostring = sprintf('%d, ', startframes);
            ids{ids_ind, 6} = starttostring(1:end-2);
            endtostring = sprintf('%d, ', endframes);
            ids{ids_ind, 7} = endtostring(1:end-2);
            %count the number of lunge bouts
            ids{ids_ind, 4} = length(startframes);
            ids{ids_ind, 5} = round(distance(i));
            %convert start time frames to seconds (assume 30fps)
            starttimetostring = sprintf('%d, ', round(startframes ./ 30));
            ids{ids_ind, 8} = starttimetostring(1:end-2);
            i = i + 1;
        end
    end
    
    %split the lunges into 60s times and write to the second excel sheet
    %first find out how many frames there are and convert to seconds
    total_len = length(postprocessed{1});
    num_mins = ceil(total_len / (30 * 60));
    ids_min = cell(12, num_mins+1);
    for i = 1:12
        ids_min{i,1} = num2str(i);
    end
    
    %should be 0, 1800, 3600,... increments of where the bouts will be
    endframes = [0, 1:num_mins]*30*60;
    
    %make a matrix to store the lunges for each fly, then sum over the 2
    %flies in the same well
    totals = zeros(24, num_mins);
    
    i = 1;
    for j = 1:24
        if ~isnan(ids_mat(j))
            %only using start frames to classify which location to classify
            startframes = tstart{i};
            ids_ind = find(ids_mat == i);
            %calculate the number of lunges within each window for each fly
            for k = 2:num_mins+1
                %index startframes in the correct window
                totals(ids_ind, k-1) = length(startframes(...
                    startframes > endframes(k-1) & startframes <= ...
                    endframes(k)));
            end
            i = i + 1;
        end
    end
    
    %now fill in for each of the 12 wells the sum of the two flies
    for minutes = 1:num_mins
        for well=1:12
            ids_min{well, minutes+1} = num2str(totals(2*well-1,minutes) + totals(2*well,minutes));
        end      
    end
    
    %create the titles for the excel sheet
    titles_min = cell(1,num_mins+1);
    titles_min{1,1} = 'Well Position';
    for i = 1:num_mins
        titles_min{1,i+1} = strcat(num2str(i-1), ' min');
    end

    %write the data to an excel file - has directory name_classifier name
    filename = strcat(directory, '\', videoname, '_', classifiername, '_Data.xlsx');
    titles = {'Well Position', 'Fly ID', 'Excluded', 'Classified Behavior Count', ...
        'Distance (mm)', 'Start Frames', 'End Frames', 'Start Times (s)'};
    output = [titles; ids];
    
    %write the main data to the first sheet and the 60s split data to the
    %second sheet
    xlswrite(filename, output, 1);   
    output_min = [titles_min; ids_min];
    xlswrite(filename, output_min, 2);
end

