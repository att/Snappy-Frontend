import subprocess

def state_num_to_name(num):
    answer = "Unknown"
    if num == 1:
        answer = "Created"
    elif num == 2:
        answer = "Done"
    elif num== 4:
        answer = "Ready"
    elif num== 8:
        answer = "Run"
    elif num== 16:
        answer = "Blocked"
    elif num== 32:
        answer = "Term."
    return answer

# translate the state number to a state name
def describe_state_column(output):

    count = 0
    newoutput = ""

    for line in output.split("\n"):
        # find the column number for the column named "state"                                                                
                           
        if count == 0:
            newoutput += line
            state_column = 0
            for w in line.split("\t"):
                if w == "state":
                    break;
                state_column += 1
        else:
            column_count = 0
            newline = ""
            for w in line.split("\t"):
                if int(column_count) == state_column:
                    newline +=  state_num_to_name(int(w)) + "\t"
                else:
                    newline += w + "\t"
                column_count += 1
            # get rid of the last tab
            newline[:-1]
            newoutput += newline
        count += 1
        newoutput += "\n"

    return newoutput
