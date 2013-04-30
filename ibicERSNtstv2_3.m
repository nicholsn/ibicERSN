% this is a trial version that adds a PowerSpectrum plot
% to work generally -- need to have the TR from call bash script
load timecoursedata.txt
input_file = fopen('sourcefilename.txt');
sourcefilename = fscanf(input_file, '%s', 1);

% gather top of noise envelope using transpose of the csv
top = max(timecoursedata');
locat = find(top > 9);
p = size(locat);
p(2) % numspikes output

% gather bottom of noise envelope using tranpose of the csv
bottom = min(timecoursedata');
lastvol = size(top); % how many volumes
x = zeros(1,2*lastvol(2));
y = zeros(1,2*lastvol(2));

% fill in x and y with top/bottom values
x(1:lastvol(2)) = 1:lastvol(2);
x(lastvol(2)+1:2*lastvol(2)) = lastvol(2):-1:1;

y(1:lastvol(2)) = top;
% bottom is addressed backwards since top drawn first
y(lastvol(2)+1:2*lastvol(2)) = bottom([lastvol(2):-1:1]);

% plotting configuration
low = min(-5, min(bottom));
high = max(10, max(top));
fill(x,y,'b'); % draws the polygon and fills in with blue ('b')
axis([0,lastvol(2)+2, low, high ]);

title(strcat("Scanner Noise Envelope for file:", sourcefilename))
xlabel("Volumes")
print ScannerNoiseEnvelope.png -dpng -FTimes-Roman:20 "-S800,600"

% start powerfreq analysis
load freqpowerdata.txt
top = max(timecoursedata');
[dum, numfreqbins] = size(top);
TR = 2;
nyquist = (1/2)*(1/TR);
x = [(nyquist/numfreqbins):(nyquist/numfreqbins):nyquist];
plot (x,top);
title(strcat("ERSN Max Power Spectrum for file:", sourcefilename));
xlabel("frequency (Hz)");
print ERSNMaxPowerSpectrum.png -dpng -FTimes-Roman:20 "-S800,600"

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


