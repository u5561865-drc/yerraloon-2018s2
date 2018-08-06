close all; clear all;clc;
%% Simulink variables
% size of box [x,y,z] assume @ origin
% legnth of propeller arms 
% length of cord
Work = trapz(controlInput);
Power = Work/4; 