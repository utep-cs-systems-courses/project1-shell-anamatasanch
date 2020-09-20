#! /usr/bin/env python3

import os, sys, time, re, fileinput


def redirect(command):
	if ">" in command:
		os.close(1)
		os.open(command[command.index('>') + 1], os.O_CREAT | os.O_WRONLY)
		os.set_inheritable(1, True)
		command.remove(">")
	
	elif "<" in command:
		os.close(0)
		os.open(command[command.index('<') + 1], os.O_RDONLY)
		os.set_inheritable(0, True)
		command.remove("<")

	for dir in re.split(":", os.environ["PATH"]):
		program = "%s/%s" % (dir, command[0])
		try:
			os.execve(program, command, os.environ)
		except FileNotFoundError:  
			pass  #keep trying

	os.write(2, ("Command not found \n").encode())
	sys.exit(1)

def execute(command):
	if ">" in command or "<" in command:
		redirect(command)
	
	elif "/" in command[0]:
		try:
			os.execve(command[0], command, os.environ)
		except FileNotFoundError:
			pass
	
	else:
		for dir in re.split(":", os.environ["PATH"]):
			program = "%s/%s" % (dir, command[0])
			try:
				os.execve(program, command, os.environ) 
			except FileNotFoundError:
				pass #keep trying

	os.write(2, ("command %s not found \n" % (command[0])).encode())
	sys.exit(1)

def pipe(command):	
	write = command[0:command.index("|")]
	read = command[command.index("|") + 1:]

	pr,pw = os.pipe()
	rc = os.fork()

	if rc < 0:
		os.write(2, ("fork failed, returning %d\n" % rc).encode())
		sys.exit(1)
	elif rc == 0:                   #  child - will write to pipe
		os.close(1)                 # redirect child's stdout
		os.dup(pw)
		os.set_inheritable(1, True) #attach stoud to pipe inheritable
		for fd in (pr, pw):
			os.close(fd)
		execute(write)
		os.write(2, ("Could not execute").encode())
		sys.exit(1)
	else:                           # parent (forked ok)
		os.close(0)
		os.dup(pr)
		os.set_inheritable(0, True) #attach stin to pipe inheritable
		for fd in (pw, pr):
			os.close(fd)
		if "|" in read:
			pipe(read)
		execute(read)
		os.write(2, ("Could not execute").encode())
		sys.exit(1)

def readCommand(command):
	if command[0] == 'exit':
		sys.exit()
	
	elif command[0] == 'cd':
		try:
			if len(command) == 2:
				os.chdir(command[1])
		except FileNotFoundError:
			os.write(2, ("The directory " + command[1] + " does not exist.").encode())
		except:
			os.write(2, ("Please enter a valid directory").encode())
	
	elif "|" in command:
		pipe(command)
		pass
	else:
		pid = os.getpid()               # get and remember pid
		rc = os.fork()
		
		if rc < 0:
			os.write(2, ("fork failed, returning %d\n" % rc).encode())
			sys.exit(1)
		elif rc == 0:                   # child
			execute(command)
			sys.exit(0)
		else:                           # parent (forked ok)
			if "&" not in command:
				val = os.wait()
				if val[1] != 0 and val[1] != 256:
					os.write(1, ("Program terminated with exit code: %d\n" % val[1]).encode())

def menu():
	while True:
		prompt = '$ '
		
		#Check PS1
		if 'PS1' in os.environ:
			prompt = os.environ['PS1']

		#File descriptor 1 is stdout
		os.write(1, prompt.encode())
		#File descriptor 0 is stdin
		userin = os.read(0, 10000)
		
	
		lines = re.split(b"\n", userin)
		
		if len(lines)>0:
			for line in lines:
				line = line.decode()
				split_line = line.split()
				if len(split_line)>0:
					readCommand(split_line)
		break 

if __name__ == "__main__":
    menu()