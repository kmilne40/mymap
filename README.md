# MyMap -- Nmap wrapper

MyMap is a Python script written by Kev to automate many of the common tasks we encounter with Nmap

In the config file (config.json) settings which can get clunky can be altered:

    output_ask - should it ask if you want to output the results to file? 
        0 = no, 1 = yes.
    output_default - if output_ask is set to 0, what option should it default to? 
        0 = no file output, 1 = outputting to file.

    screen_output_ask - should it ask if you want the output to be shown on screen? 
        0 = no, 1 = yes.
    screen_output_default - if screen_output_ask is set to 0, what option should it default to? 
        0 = no screen output, 1 = output to screen.

    report_ask - should it ask if you want a report to be generated? 
        0 = no, 1 = yes.
    report_default - if report_ask is set to 0, what option should it default to? 
        0 = no report, 1 = generate report.
    
    speed_dial_ask - should it ask if you want to add a command to speed dial after a completed scan?
        0 = no, 1 = yes.    

Scans saved in the speed dial are contained within the same config.json file, for example "http": "-p 80", being a speed dial scan named http and using the '-p 80' argument. If speed_dial_ask is set to 1, you will be prompted if you want to save the last command to speed dial. This currently works for all commands built through the search feature and custom commands that used an IP address as the target.
