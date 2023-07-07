Assignment 1 By Prashanth Sriram S (CS20BTECH11039) For CN3530 course:
------------------------------------------------------------------------
1. SUBMISSION CONTENTS:
-----------------------
The zip file CS20BTECH11039_Assignment1.zip has two folder basic and star and each folder has its own report as a pdf inside.
Each folder also have the pcap files to be submitted inside another directory. Structure:
Zip
|----Basic:
        |----AssignmentPcapFolder
                    |----pcap files(one for GET, one for PUT, one for DELETE and 6 pcap files for 3 gets of 6 keys)
        |--- python files and p4 files and make files
        |--- report for basic topology
|----Star:
        |----AssignmentPcapFolder
                    |----pcap files[(one file for h1, one for h2 and one for h3 for two gets) and then a pcap file for 6 gets of keys 3 times]
        |---python files and p4 files and make files
        |---report for star topology (report for web cache server)

This readme is both submitted along with the zip and the zip also contains this same readme

2. RUNNING INSTRUCTIONS:
-------------------------
To run them: run make clean, then make run and then do xterm h1, xterm h2 and xterm h3(for the webcache case) and then run bash h1-... or bash h2-... or bash h3-.. files on the terminal opened for h1, h2 and h3 respectively and then run python clinet.py on h1 and for the basic case, server.py on h2, and for the star case, cache.py on h2 and server.py on h3

Interface for the client.py: The only place that needs user interaction:
It prompts for 1.GET 2.PUT 3.DELETE 4.EXIT and you have to enter 1 or 2 or 3 or 4. then follow the instructions given by the prompt. 
For GET, just enter the key. and for PUT, enter key<space>value. For DELETE, just enter the key

Same interface of client.py in both basic and star, except star doesn't have 3.DELETE functionality
