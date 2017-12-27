import sys
sys.path.append("/Users/nihar/Nihar/SAIL/gentle")
sys.path.append("/Users/nihar/Nihar/SAIL/gentle/gentle")
sys.path.append("/home/kian/ML/SAIL/sail-forensic-gentle/gentle")
sys.path.append("/home/kian/ML/SAIL/sail-forensic-gentle/gentle/gentle")
import gentle

from segment import Segment
from pydub import AudioSegment
reload(sys)
sys.setdefaultencoding('utf-8')


import os
import json

def run_gentle(seg):
	"""
	takes in a segment
	1. create new text file containing text
	2. create new audio with pydub
	3. run Gentle with these two
	4. delete text file/audio files
	"""
	# transcript = " ".join(seg.get_text())
	transcript = "I am sitting in a room different from the one you are in now. I am recording the sound of my speaking voice and I am going to play it back into the room again and again until the resonant frequencies of the room reinforce themselves so that any semblance of my speech, with perhaps the exception of rhythm, is destroyed. What you will hear, then, are the natural resonant frequencies of the room articulated by speech. I regard this activity not so much as a demonstration of a physical fact, but more as a way to smooth out any irregularities my speech might have."

	# I think they are wav files, but not sure
	# audio_full = AudioSegment.from_file(seg.audio_file, format="mp3")
	audio_cut = seg.audio_file[seg.start_audio:seg.end_audio]
	
	audio_cut.export("temp_audio.wav", format="wav", codec="libmp3lame")

	# run Gentle
	resources = gentle.Resources()
	with gentle.resampled("temp_audio.wav") as wavfile:
		aligner = gentle.ForcedAligner(resources, transcript)
		result = aligner.transcribe(wavfile)

	# delete cut audio file
	os.remove("temp_audio.wav")

	return result


def segmentize (gentle_outputs, audio_file, 
				anchor_length=3, rel_audio_start=0):
	"""
	takes in Gentle output (list of Word objects)
	break into segments which marked as aligned or unaligned
	"""
	correct_count = 0
	end_prev_anchor = 0

	# stores index of first correct point in a series
	first_correct_index = None

	# store all segments
	segs = []

	# run through the list of gentle output dictionaries
	for index, word in enumerate(gentle_outputs):
		# if the word was successfully aligned
		if word.success():
			# update variable values and move on
			correct_count += 1
			
			# update first_correct tracker
			if first_correct_index is None:
				first_correct_index = index	


		# if unaligned check if there are enough correct for anchor
		elif correct_count >= anchor_length:
			
			#check if there is an unaligned seg before anchor point
			if end_prev_anchor != first_correct_index:
				# store the previous unanchored segments as a seg and append
				seg = get_segment(gentle_outputs[end_prev_anchor: \
					first_correct_index], rel_audio_start, False, audio_file)	
				segs.append(seg)

			# store the anchor segment
			seg = get_segment(gentle_outputs[first_correct_index: \
				index], rel_audio_start, True, audio_file)
			segs.append(seg)	
			
			# update end of prev anchor tracker
			end_prev_anchor = index

			# reset counter variables
			correct_count = 0
			first_correct_index = None

		
		#if we have reached the end of the audio file
		#we need to segmentize all the remaining
		#unsegmented part of the transcript/audiofile
		if index == len(gentle_outputs) - 1:

			#if current seg is an anchor point ...
			if correct_count >= anchor_length:

				
				# store the previous unanchored segments as a seg and append
				seg = get_segment(gentle_outputs[end_prev_anchor: \
					first_correct_index], rel_audio_start, False, audio_file)	
				segs.append(seg)	

				
				
				# store the anchor segment
				seg = get_segment(gentle_outputs[first_correct_index:], \
					rel_audio_start, True, audio_file)
				segs.append(seg)	
				
				# update end of prev anchor tracker
				end_prev_anchor = index
			
			#if current segment does not qualify as an anchor point
			else:

				#check if there is an unaligned seg before anchor point
				if end_prev_anchor != first_correct_index:
					# store the previous unanchored segments as a seg- append
					seg = get_segment(gentle_outputs[end_prev_anchor:], \
						rel_audio_start, False, audio_file)	
					segs.append(seg)

	return segs


def fix_unaligned (gentle_output, audio_file):
	"""
	Give approximate start/end times to unaligned words in the Gentle output.

	Parameters
	----------
	gentle_output: list of Word objects returned by Gentle
	audio_file: AudioSegment object representing the entire audio file
	"""
	initialStart = 0
	for word in gentle_output:
		if not word.success():
			word.start = initialStart
		else:
			initialStart = word.end

	initialEnd = len(audio_file)
	for word in gentle_output[::-1]:
		if not word.success():
			word.end = initialEnd
		else:
			initialEnd = word.start


def get_segment (gentle_output, rel_audio_start, aligned, audio_file):

	# relative audio start time plus the audio time of the first/last word
	audio_start = rel_audio_start + gentle_output[0].start
	audio_finish = rel_audio_start + gentle_output[-1].end

	seg = Segment(audio_start, audio_finish,
				  gentle_output, aligned, audio_file)
	
	return seg

testAudio = AudioSegment.from_file("/home/kian/ML/SAIL/sail-forensic-gentle/gentle/examples/data/lucier.mp3")
seg = Segment(0, len(testAudio), [], True, testAudio)
transcript_object = run_gentle(seg)
words = transcript_object.words
fix_unaligned(words, testAudio)


segs = segmentize(words, "/home/kian/ML/SAIL/sail-forensic-gentle/gentle/examples/data/lucier.mp3")
for seg in segs:
	print(seg.start_audio, seg.end_audio, seg.aligned)
