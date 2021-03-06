Push Scripts
============

## Script Overview
The script *start_Push.py* takes as input a CSV (See example below) which has all of the run or sample information necessary to push or copy sequencing files of a sample from a Torrent Suite sequencing PGM or Proton to a specific project/sample/run directory on another server. 

> Important note: This is simply a push script meaning only files where the script is located and run can be copied to another location.   


### Prepare the CSV
Here is an example excel document from the Wales project used to push the data from the Yale PGM to TRI's triton:

**Germline only project exapmle:**

| Sample    | Run ID | Run # | Barcode       | Sequencing Machine |
|-----------|--------|-------|---------------|--------------------|
| case1_A01 |      1 |   291 | IonXpress_001 | ROT                |
| case1_A02 |      1 |   327 | IonXpress_002 | ROT                |
| case1_A03 |      1 |    18 | IonXpress_003 | ROT                |

Here is that same file after exporting it as a CSV from excel:  
Sample,Run ID, Run #, Barcode,Sequencing Machine  
case1_A01,1,291,IonXpress_001,ROT  
case1_A02,1,327,IonXpress_002,ROT  
case1_A03,1,18,IonXpress_003,ROT  

**Tumor/Normal example:**

| Sample # | Normal (N) vs Tumor(T) | Run ID  | Run # | Barcode       |
|----------|------------------------|---------|-------|---------------|
| A_286    | N                      | PLU-338 |     1 | -             |
| A_286    | N                      | MER-207 |     5 | -             |
| A_286    | T                      | PLU-515 |     3 | IonXpress_078 |

Sample #,Normal (N) vs Tumor(T),Run ID,Run #,Barcode Used  
A_286,N,PLU-338,1,-  
A_286,N,MER-207,5,-  
A_286,T,PLU-515,3,IonXpress_078  

This is the format of the input to _start\_Push.py_. If no barcodes are provided, then the script will adapt accordingly. If the "Sequencing Machine" three letter code is in the Run ID, it will be parsed from there. Otherwise, it will be parsed from the last column. Three letter codes we use: PLU, NEP, MER, ROT.

> Important Note:  If using a mac, excel will add a funny character to the end of the line on a CSV. This will cause linux to read the file incorrectly. To prep the CSV for linux, open the CSV in [_vim_](file:///tmp/d20150412-3-m06vk1/Bioinformatics_Glossary.docx#Vim) and type the following two commands:
> `:set fileformat=unix` and `:%s/\r/\r/g`

**Server Information:** If you are pushing a large number of runs from one server to another, you do not want to have to type in the password for every file that is copied. See [Passwordless SSH Keys](https://github.com/jlaw9/TRI_Dev/wiki/Passwordless-SSH-Keys) for instructions on how to store an ssh-key from one server to another to bypass having to enter a password.


### Push the Files
**Step 1:** Run _start\_Push.py_ giving the new server IP address, the destination path where the files should be placed on the new server, the CSV, and the log file. **_start\_Push.py_ will run all of the next steps.**

	python start_Push.py --help
	Options:
	  -h, --help            show this help message and exit
	  -s SERVER, --server=SERVER
	                        Required. The server to push data to.
	                        <ionadmin@ipaddress>
	  -d DESTINATION, --destination=DESTINATION
	                        Required. The destination path where the sample will
	                        be copied to.
	  -i INPUT, --input=INPUT
	                        Required. The input csv file containing the metadata
	                        about each sample to be pushed.
	  -j EX_JSON, --ex_json=EX_JSON
	                        Required. The example json file containing the
	                        settings necessary for this project. Should be
	                        different for every project. For help of how to create
	                        the example json file, see the protocls
	  -p PROTON, --proton=PROTON
	                        Required. The name of the proton or pgm from which you
	                        are pushing the files. Options: "PLU", "MER", "NEP,
	                        "ROT"
	  -H, --header          use this option if the CSV has a header line.
	  -o OUTPUT_CSV, --output_csv=OUTPUT_CSV
	                        The results of copying will be placed in this file.
	                        Default: [Push_Results.csv]
	  -l LOG, --log=LOG     Default: [Push.log]
	  -R RUN_ANYWAY, --run_anyway=RUN_ANYWAY
	                        if the server is not in the list of "accepted
	                        servers", push the data anyway


**Step 2:** Parse the input file line by line and will store the info of each column separated by a comma. _start\_Push.sh_ will then call _push_Data.sh_ for each line of the CSV to actually transfer the files.

	bash push_Data.sh
		--user_server ionadmin@ipaddress
		--project_path /dest/path/on/new/server
		--sample E0001
		--run_id 468 (the run ID from the CSV)
		--run Run1
		--proton_name PLU (either PLU or MER)
		--backup_path $BACKUP_PATH
		>> push_results.csv </dev/null &


**Step 3:** Generate a JSON file containing this run's info using _writeJson.py_. This JSON file will be used throughout the pipeline to store important run metrics and metadata. See the protocol [_Automated\_Scripts.docx_](file:///tmp/d20150412-3-m06vk1/Automated_Scripts.docx)file for an explanation of how the JSON file is used. Each of the metrics passed into _writeJson.py_ either from the CSV used as input or from the settings used to call _start\_push.py_ will be added to the json file.

	python writeJson.py
		--bam E0001.bam
		--run_name Run1
		--sample E0001
		--proj_path /dest/path/on/new/server
		--orig_path /path/where/bam/file/was/found
		--proton PLU or MER
		--ip_address 192.168.200.42 (IP address of Triton)
		--ts_version 4.2 (TS version used to generate the BAM file. This information is found in the version.txt file)
		--json E0001_Run1.json (JSON file to be made)


An important note here is that if you are pushing this data to a new server, the settings found in [_writeJson.py_](https://github.com/jlaw9/Scripts/blob/master/Push/writeJson.py) from line 38-45 will need to be edited to represent the correct new paths to each file found on the new server.

**Step 4:** Find the following files and prepare them to be copied. If the rawlib.bam is found in the non-archived directory, the following files will be copied from there. Otherwise, they will be copied from the archived location on the server (for pluto: /mnt/Charon/archivedReports for mercury: /mnt/Triton/archivedReports).

- rawlib.bam
- rawlib.bam.bai
- E0001\_Run1.json
- E0001.amplicon.cov.xls (This will only be copied if Coverage Analysis was run on the browser)
- TSVC\_variants.vcf (This will only be copied if TVC was run on the browser)
- report.pdf (Contains the run metrics such as % polyclonality. Will be parsed later in the process.)

**Step 5:** Copy (push) the files to the new server using [rsync](file:///tmp/d20150412-3-m06vk1/Bioinformatics_Glossary.docx#rsync). Files are copied one at a time to the new server. If the file already exists on the new server, the file will not be re-copied. If the copy is successful, the script prints a successful message to the log file. If the file transfer is unsuccessful either because of a lost connection or some other reason, the script will try again in 30 seconds up to 10 times. After that, if the copy is still unsuccessful, the script will print an error message to the log file and continue copying the other files listed in the CSV.

	rsync -avz --progress E0001.bam $Triton:/path/to/E0001.bam

**Step 6:** Check the log *push_results.csv* file to ensure that all of the files were copied correctly. If any files are not copied properly, they might have to be manually copied using [_rsync_](file:///tmp/d20150412-3-m06vk1/Bioinformatics_Glossary.docx#rsync) or [_scp_](file:///tmp/d20150412-3-m06vk1/Bioinformatics_Glossary.docx#scp).
