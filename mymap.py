#!/usr/bin/python

import os
import subprocess
import time
import re
import json

from tqdm import tqdm
from termcolor import colored

from getters import get_scripts, get_port, get_target
from printers import print_menu, print_sub_menu, generate_report, view_output, print_script_description

def load_config(config_path='config.json'):
    if not os.path.isfile(config_path):
        print(colored(f"Config file {config_path} not found.", "red"))
        return {}
    try:
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    except json.JSONDecodeError:
        print(colored(f"Error decoding JSON from {config_path}.", "red"))
        return {}

def read_config(config_data, option):
    return config_data.get("configuration", {}).get(option, 0)

def run_nmap_with_progress(args_list):
    """
    Run nmap with given arguments plus --stats-every for progress.
    Capture output line by line, display progress when found.
    Return full output at the end.
    """
    # Add --stats-every 5s to get periodic progress
    if "--stats-every" not in args_list:
        args_list += ["--stats-every", "5s"]

    cmd = ["nmap"] + args_list
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    full_output = []
    progress_regex = re.compile(r'About\s+(\d+(\.\d+)?)%\s+done')

    last_percentage = 0
    start_time = time.time()

    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            full_output.append(line)
            # Check for progress line
            match = progress_regex.search(line)
            if match:
                percent = match.group(1)
                try:
                    percent_val = float(percent)
                    # Only print if percent increased
                    if percent_val > last_percentage:
                        print(colored(f"Progress: {percent_val:.2f}% done", "cyan"))
                        last_percentage = percent_val
                except ValueError:
                    pass

    retcode = process.poll()
    if retcode != 0:
        print(colored(f"Error running nmap: return code {retcode}", "red"))
        return None
    return "".join(full_output)

def run_script(script, target, port, output_file, config_data):
    if os.path.isfile(target):
        target_option = ["-iL", target]
        run_target = []
    else:
        target_option = []
        run_target = [target]

    script_path = f"/usr/share/nmap/scripts/{script}"
    if not os.path.exists(script_path):
        print(colored(f"Script {script} not found at {script_path}", "red"))
        return None

    base_args = ["-T4", port, "--script", script_path]
    if output_file:
        base_args += ["-oN", output_file]

    args = base_args + target_option + run_target
    return run_nmap_with_progress(args)

def get_output_file(config_data):
    output_ask = read_config(config_data, 'output_ask')
    output_default = read_config(config_data, 'output_default')
    output_file = ""

    if output_ask == 1:
        while True:
            choice = input(colored("\nDo you want to output to file? (y/n): ", "yellow")).strip().lower()
            if choice in ["y", "yes"]:
                output_file = input(colored("\nEnter output file (leave blank for default): ", "yellow")).strip()
                if output_file == "":
                    timestr = time.strftime("%Y_%m_%d-%I_%M_%S_%p")
                    output_file = timestr + ".txt"
                    print(colored(f"\nDefault output file: {output_file}", "green"))
                break
            elif choice in ["n", "no"]:
                output_file = ""
                break
            else:
                print(colored("Invalid option", "red"))
    else:
        if output_default == 1:
            output_file = input(colored("\nEnter output file (leave blank for default): ", "yellow")).strip()
            if output_file == "":
                timestr = time.strftime("%Y_%m_%d-%I_%M_%S_%p")
                output_file = timestr + ".txt"
                print(colored(f"\nDefault output file: {output_file}", "green"))
        else:
            output_file = ""

    return output_file

def get_screen_output(output, config_data):
    screen_output_ask = read_config(config_data, 'screen_output_ask')
    screen_output_default = read_config(config_data, 'screen_output_default')
    view_choice = "n"

    if screen_output_ask == 1:
        while True:
            choice = input(colored("\nDo you want to view the output? (y/n): ", "yellow")).strip().lower()
            if choice in ["y", "yes"]:
                view_output(output)
                view_choice = "y"
                break
            elif choice in ["n", "no"]:
                break
            else:
                print(colored("Invalid option", "red"))
    else:
        if screen_output_default == 1:
            view_output(output)
            view_choice = "y"

    return view_choice

def report_stuff(output, script, target, output_file, view_choice, config_data):
    report_ask = read_config(config_data, 'report_ask')
    report_default = read_config(config_data, 'report_default')

    if report_ask == 1:
        while True:
            choice = input(colored("Do you want to generate a penetration testing report? (y/n): ", "yellow")).strip().lower()
            if choice in ["y", "yes"]:
                generate_report(output, script, target, output_file, view_choice)
                break
            elif choice in ["n", "no"]:
                break
            else:
                print(colored("Invalid option", "red"))
    else:
        if report_default == 1:
            generate_report(output, script, target, output_file, view_choice)

def search(scripts, config_data):
    search_results = []
    while not search_results:
        search_term = input(colored("\nEnter a search term (max 8 chars):\n-> ", 'yellow'))[:8]
        search_results = [script for category in scripts for script in scripts[category] if search_term in script]
        if not search_results:
            print(colored('\nNO RESULTS', "red"))

    print_sub_menu("Search Results", search_results)

    choice = input(colored("\nChoose script by number, 's' to search again, '0' to menu:\n-> ", 'yellow')).strip().lower()
    while choice != 's' and (not choice.isdigit() or int(choice) < 0 or int(choice) > len(search_results)):
        print(colored("\nInvalid choice. Please try again.", "red"))
        choice = input(colored("\nChoose script or 's' to search again, '0' for menu:\n-> ", 'yellow')).strip().lower()

    if choice == 's':
        search(scripts, config_data)
        return
    elif choice == '0':
        return
    else:
        choice = int(choice)
        print_script_description(search_results[choice-1])
        target = get_target()
        port = get_port()
        output_file = get_output_file(config_data)
        output = run_script(search_results[choice-1], target, port, output_file, config_data)

        if output:
            view_choice = get_screen_output(output, config_data)
            report_stuff(output, search_results[choice-1], target, output_file, view_choice, config_data)

        if read_config(config_data, 'speed_dial_ask') == 1:
            ask_to_add_to_speed_dial(config_data)

def run_custom_command(config_data):
    print(colored("\nExample: nmap <target> -p 80 -sV -O", "blue"))
    user_cmd = input(colored("Enter your custom Nmap command (without 'nmap'):\n-> nmap ", "yellow")).strip()

    bad_chars = [';', '&', '>', '|']
    if any(badchar in user_cmd for badchar in bad_chars):
        print(colored("Potential command injection detected. Aborting.", "red"))
        return

    args = user_cmd.split()
    output_file = get_output_file(config_data)
    if output_file:
        args += ["-oN", output_file]

    # Run nmap with progress
    output = run_nmap_with_progress(args)
    if output:
        view_choice = get_screen_output(output, config_data)
        report_stuff(output, user_cmd, "", output_file, view_choice, config_data)

    ip_pattern = r'((\d{1,2}|1\d{2}|2[0-4]\d|25[0-5])\.){3}(\d{1,2}|1\d{2}|2[0-4]\d|25[0-5])$'
    if re.search(ip_pattern, user_cmd):
        remove_target = re.sub(ip_pattern, '', user_cmd)
        ask_to_add_to_speed_dial(config_data, custom=True, last=remove_target)
    else:
        print(colored("Cannot add to speed dial automatically (no direct IP found).", "yellow"))

def ask_to_add_to_speed_dial(config_data, custom=False, last=""):
    while True:
        prompt = "Add last command to speed dial? (y/n): "
        choice = input(colored(prompt, "yellow")).strip().lower()
        if choice in ["y", "yes"]:
            title = input(colored("Name this scan for speed dial: ","yellow")).strip()
            add_to_speed_dial(config_data, title, last)
            break
        elif choice in ["n", "no"]:
            break
        else:
            print(colored("Invalid option","red"))

def add_to_speed_dial(config_data, title, flags):
    if "speed_dial" not in config_data:
        config_data["speed_dial"] = {}
    config_data["speed_dial"][title] = flags
    with open('config.json','w') as config_file:
        json.dump(config_data, config_file, indent=4)
    print(colored("\nSpeed dial saved.", "green"))

def speed_dial(config_data):
    print("\nSPEED DIAL MENU: Quick access to saved commands.")

    while True:
        dials = config_data.get("speed_dial", {})
        if not dials:
            print(colored("\nNo speed dial options.", "red"))
        else:
            content = [f"{i+1}. {k}: {v}" for i,(k,v) in enumerate(dials.items())]
            print_sub_menu("Saved", content)
        
        option = input(colored("\nENTER:\nNumber of speed dial\n'a' add\n'e' erase\n'0' back\n-> ", "yellow")).strip().lower()
        if option == "0":
            return
        elif option == "a":
            flags = ""
            while True:
                flags = input(colored("\nEnter flags/options (no target):\n-> ", "yellow")).strip()
                if flags:
                    break
            while True:
                title = input(colored("\nEnter a title:\n-> ", "yellow")).strip()
                if title and title not in dials:
                    add_to_speed_dial(config_data, title, flags)
                    break
                else:
                    print(colored("Invalid title or title already exists.", "red"))
        elif option == "e":
            if not dials:
                continue
            to_delete = input(colored("\nEnter number to delete or 0 to cancel:\n-> ", "yellow")).strip()
            if to_delete == "0":
                continue
            if to_delete.isdigit():
                idx = int(to_delete)-1
                if 0 <= idx < len(dials):
                    key_to_del = list(dials.keys())[idx]
                    del config_data["speed_dial"][key_to_del]
                    with open('config.json','w') as config_file:
                        json.dump(config_data, config_file, indent=4)
                    print(colored(f"\nDeleted speed dial {to_delete}.", "green"))
                else:
                    print(colored("Invalid number.", "red"))
            else:
                print(colored("Invalid input.", "red"))
        elif option.isdigit():
            idx = int(option)-1
            if idx < 0 or idx >= len(dials):
                print(colored("Invalid choice.", "red"))
            else:
                key = list(dials.keys())[idx]
                flags = dials[key]
                target = get_target()
                if os.path.isfile(target):
                    target_option = ["-iL", target]
                    run_target = []
                else:
                    target_option = []
                    run_target = [target]

                output_file = get_output_file(config_data)
                cmd = ["nmap"] + target_option + run_target + flags.split()
                if output_file:
                    cmd += ["-oN", output_file]

                # Progress may not be possible here unless we add --stats-every again
                # Add stats and run with progress:
                if "--stats-every" not in cmd:
                    cmd += ["--stats-every", "5s"]
                output = run_nmap_with_progress(cmd[1:]) # pass arguments without 'nmap'

                if output:
                    view_choice = get_screen_output(output, config_data)
                    report_stuff(output, " ".join(cmd[1:]), "", output_file, view_choice, config_data)
        else:
            print(colored("Invalid choice.", "red"))

def config_checkup(config_data):
    while True:
        configuration = config_data.get("configuration", {})
        content = [f"{i+1}. {k}: {v}" for i,(k,v) in enumerate(configuration.items())]

        print_sub_menu("Current Configuration", content)
        option = input(colored("\nENTER:\nNumber to edit\n'0' back\n-> ", 'yellow')).strip()

        if option == "0":
            return
        if not option.isdigit():
            print(colored("Invalid option.", "red"))
            continue

        idx = int(option)-1
        if idx < 0 or idx >= len(configuration):
            print(colored("Invalid option.", "red"))
            continue
        key = list(configuration.keys())[idx]
        new_value = input(colored("\nSet value (1 or 0):\n-> ", "yellow")).strip()
        while new_value not in ["0","1"]:
            print(colored("Invalid. Must be 0 or 1", "red"))
            new_value = input(colored("\nSet value (1 or 0):\n-> ", "yellow")).strip()

        config_data["configuration"][key] = int(new_value)
        with open('config.json','w') as config_file:
            json.dump(config_data, config_file, indent=4)
        print(colored("\nConfig saved.", "green"))

def get_info_run_script(scripts, script_index, config_data):
    script_name = scripts[script_index-1]
    print_script_description(script_name)
    target = get_target()
    port = get_port()
    output_file = get_output_file(config_data)
    output = run_script(script_name, target, port, output_file, config_data)

    if output:
        view_choice = get_screen_output(output, config_data)
        report_stuff(output, script_name, target, output_file, view_choice, config_data)

    if read_config(config_data, 'speed_dial_ask') == 1:
        ask_to_add_to_speed_dial(config_data)

def choose_script_from_category(scripts, digit, config_data):
    if 1 <= digit <= len(scripts):
        category = list(scripts.keys())[digit-1]
        print_sub_menu(category, scripts[category])
        script_choice = input(f"\nChoose a script from {category} by number or '0' back: ").strip()
        if script_choice == "0":
            return
        if not script_choice.isdigit():
            print(colored("Invalid choice.", "red"))
            return
        script_choice = int(script_choice)
        if script_choice < 1 or script_choice > len(scripts[category]):
            print(colored("Invalid choice.", "red"))
            return
        get_info_run_script(scripts[category], script_choice, config_data)
    else:
        print(colored("Invalid category choice.", "red"))

def show_help():
    help_file = 'help.txt'
    if not os.path.isfile(help_file):
        print(colored("Help file not found.", "red"))
        return
    with open(help_file, 'r') as hf:
        content = hf.read()
    print(colored("\n=== HELP INFORMATION ===", "cyan"))
    print(content)
    print(colored("=== END OF HELP ===\n", "cyan"))
    input(colored("Press ENTER to return to menu...", "yellow"))

def main():
    config_data = load_config('config.json')
    print(colored("=================================\n      WELCOME TO... MYMAP!", "magenta"))
    print(colored("  A wrapper for nmap by Kev,", "green"))
    print(colored(" modified, with improvements by", "green"))
    print(colored("Hubert Januszewski and Sophie Hall:))", "green"))
    print(colored("==================================", "magenta"))

    scripts = get_scripts()

    while True:
        print_sub_menu("SCRIPT CATEGORIES", list(scripts.keys())[:10])
        category_choice = input(colored("\nOR ENTER:\n- number of script category\n- 's' search\n- 'c' custom\n- 'd' speed dial\n- 'e' edit settings\n- 'h' help\n- 'q' quit\n-> ", 'yellow')).strip().lower()

        if category_choice == 'q':
            break
        elif category_choice == 's':
            search(scripts, config_data)
        elif category_choice == 'c':
            run_custom_command(config_data)
        elif category_choice == 'd':
            speed_dial(config_data)
        elif category_choice == 'e':
            config_checkup(config_data)
        elif category_choice == 'h':
            show_help()
        elif category_choice.isdigit():
            choose_script_from_category(scripts, int(category_choice), config_data)
        else:
            print(colored("\nInvalid Option!","red"))

    print(colored("\nGoodbye!","green"))

if __name__ == "__main__":
    main()
