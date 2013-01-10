load timecoursedata.txt
input_file = fopen('sourcefilename.txt');
sourcefilename = fscanf(input_file, '%s', 1);

top = max(timecoursedata');
locat = find(top > 9);
p = size(locat);
p(2)

bottom = min(timecoursedata');
lastvol = size(top);
x = zeros(1,2*lastvol(2));
y = zeros(1,2*lastvol(2));

x(1:lastvol(2)) = 1:lastvol(2);
x(lastvol(2)+1:2*lastvol(2)) = lastvol(2):-1:1;

y(1:lastvol(2)) = top;
y(lastvol(2)+1:2*lastvol(2)) = bottom([lastvol(2):-1:1]);

low = min(-5, min(bottom));
high = max(10, max(top));
fill(x,y,'b');
axis([0,lastvol(2)+2, low, high ]);

title(strcat("Scanner Noise Envelope for file:", sourcefilename))
xlabel("Volumes")

print ScannerNoiseEnvelope.png -dpng -FTimes-Roman:20 "-S800,600"


%Old code ideas
% The following code locates the spikes by vol and IC
%spikes = zeros(p(1),2);
%for i = 1:p(1)
%q = locat(i);
% get indices of each spike
%[spikes(i,1), spikes(i,2)] = ind2sub(size(timecoursedata), q);
%endfor
%spikes;
%spikevols = sort(spikes(:,1));
%spikeICs = sort(spikes(:,2));
%dlmwrite ("spikevols.txt", spikevols, " ")
%dlmwrite ("spikeICs.txt", spikeICs, " ")
exit
