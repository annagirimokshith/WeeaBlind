import wx
import wx.adv
import sys
from tabs.ConfigureVoiceTab import ConfigureVoiceTab
from tabs.SubtitlesTab import SubtitlesTab
from tabs.ListStreams import ListStreamsTab
from tabs.GreeterView import GreeterView
import threading
import utils
from video import Video
import app_state
import feature_support
from Voice import Voice
import os

class GUI(wx.Panel):
	def __init__(self, parent):
		super().__init__(parent)

		# Define a color palette
		self.colors = {
			"background": wx.Colour(240, 240, 240), # Light grey
			"text": wx.Colour(50, 50, 50),        # Dark grey
			"accent": wx.Colour(0, 120, 215),     # Blue
			"success": wx.Colour(0, 150, 0),       # Green
			"error": wx.Colour(200, 0, 0)         # Red
		}
		self.SetBackgroundColour(self.colors["background"])

		# Define standard fonts
		self.fonts = {
			"title": wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD),
			"label": wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL),
			"input": wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		}

		lbl_title = wx.StaticText(self, label="WeeaBlind")
		lbl_title.SetFont(self.fonts["title"])
		lbl_title.SetForegroundColour(self.colors["accent"])

		lbl_GPU = wx.StaticText(self, label=f"GPU Detected? {feature_support.gpu_supported}")
		lbl_GPU.SetFont(self.fonts["label"])
		lbl_GPU.SetForegroundColour(self.colors["success"] if feature_support.gpu_supported else self.colors["error"])

		btn_choose_file = wx.Button(self, label="Choose File")
		btn_choose_file.SetFont(self.fonts["input"])
		btn_choose_file.Bind(wx.EVT_BUTTON, self.open_file)

		lbl_main_file = wx.StaticText(self, label="Choose a video file or link to a YouTube video:")
		lbl_main_file.SetFont(self.fonts["label"])
		lbl_main_file.SetForegroundColour(self.colors["text"])
		self.txt_main_file = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER, value=utils.test_video_name)
		self.txt_main_file.SetFont(self.fonts["input"])
		self.txt_main_file.SetBackgroundColour(wx.Colour(255,255,255))
		self.txt_main_file.Bind(wx.EVT_TEXT_ENTER, lambda event: self.load_video(self.txt_main_file.Value))

		lbl_dl_lang = wx.StaticText(self, label="Download subtitle language:")
		lbl_dl_lang.SetFont(self.fonts["label"])
		lbl_dl_lang.SetForegroundColour(self.colors["text"])
		self.txt_dl_lang = wx.TextCtrl(self, value="en")
		self.txt_dl_lang.SetFont(self.fonts["input"])
		self.txt_dl_lang.SetBackgroundColour(wx.Colour(255,255,255))

		lbl_start_time = wx.StaticText(self, label="Start Time:")
		lbl_start_time.SetFont(self.fonts["label"])
		lbl_start_time.SetForegroundColour(self.colors["text"])
		lbl_end_time = wx.StaticText(self, label="End Time:")
		lbl_end_time.SetFont(self.fonts["label"])
		lbl_end_time.SetForegroundColour(self.colors["text"])

		self.txt_start = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER, value=utils.seconds_to_timecode(0))
		self.txt_start.SetFont(self.fonts["input"])
		self.txt_start.SetBackgroundColour(wx.Colour(255,255,255))
		self.txt_end = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER, value=utils.seconds_to_timecode(0))
		self.txt_end.SetFont(self.fonts["input"])
		self.txt_end.SetBackgroundColour(wx.Colour(255,255,255))
		self.txt_start.Bind(wx.EVT_TEXT_ENTER, self.change_crop_time)
		self.txt_end.Bind(wx.EVT_TEXT_ENTER, self.change_crop_time)

		self.chk_match_rate = wx.CheckBox(self, label="Match Speaker Rate")
		self.chk_match_rate.SetFont(self.fonts["label"])
		self.chk_match_rate.SetForegroundColour(self.colors["text"])
		self.chk_match_rate.SetValue(True)

		self.lb_voices = wx.ListBox(self, choices=[speaker.name for speaker in app_state.speakers])
		self.lb_voices.SetFont(self.fonts["input"])
		self.lb_voices.SetBackgroundColour(wx.Colour(255,255,255))
		self.lb_voices.Bind(wx.EVT_LISTBOX, self.on_voice_change)
		self.lb_voices.Select(0)

		btn_new_speaker = wx.Button(self, label="New Speaker")
		btn_new_speaker.SetFont(self.fonts["input"])
		btn_new_speaker.Bind(wx.EVT_BUTTON, self.add_speaker)

		tab_control = wx.Notebook(self)
		# Pass colors and fonts to tabs
		greeter_tab = GreeterView(tab_control, self, colors=self.colors, fonts=self.fonts)
		tab_control.AddPage(greeter_tab, "Welcome!")
		self.tab_voice_config = ConfigureVoiceTab(tab_control, self, colors=self.colors, fonts=self.fonts)
		tab_control.AddPage(self.tab_voice_config, "Configure Voices")
		self.tab_subtitles = SubtitlesTab(tab_control, self, colors=self.colors, fonts=self.fonts)
		tab_control.AddPage(self.tab_subtitles, "Subtitles")
		self.streams_tab = ListStreamsTab(tab_control, self, colors=self.colors, fonts=self.fonts)
		tab_control.AddPage(self.streams_tab, "Video Streams")
		
		btn_run_dub = wx.Button(self, label="Run Dubbing!")
		btn_run_dub.SetFont(self.fonts["input"])
		btn_run_dub.SetBackgroundColour(self.colors["accent"])
		btn_run_dub.SetForegroundColour(wx.Colour(255,255,255)) # White text
		btn_run_dub.Bind(wx.EVT_BUTTON, self.run_dub)

		# Main vertical sizer
		main_sizer = wx.BoxSizer(wx.VERTICAL)

		# Title and GPU status
		title_sizer = wx.BoxSizer(wx.HORIZONTAL)
		title_sizer.Add(lbl_title, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)
		title_sizer.AddStretchSpacer(1)
		title_sizer.Add(lbl_GPU, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)
		main_sizer.Add(title_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

		main_sizer.AddSpacer(10)

		# File input section
		main_sizer.Add(lbl_main_file, 0, wx.LEFT | wx.TOP, 10)
		file_input_sizer = wx.BoxSizer(wx.HORIZONTAL)
		file_input_sizer.Add(self.txt_main_file, 1, wx.EXPAND | wx.RIGHT, 5)
		file_input_sizer.Add(btn_choose_file, 0, wx.ALIGN_CENTER_VERTICAL)
		main_sizer.Add(file_input_sizer, 0, wx.EXPAND | wx.ALL, 10)

		# Download language
		dl_lang_sizer = wx.BoxSizer(wx.HORIZONTAL)
		dl_lang_sizer.Add(lbl_dl_lang, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		dl_lang_sizer.Add(self.txt_dl_lang, 1, wx.EXPAND)
		main_sizer.Add(dl_lang_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
		
		# Time crop section
		time_crop_sizer = wx.BoxSizer(wx.HORIZONTAL)
		time_crop_sizer.Add(lbl_start_time, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		time_crop_sizer.Add(self.txt_start, 1, wx.EXPAND | wx.RIGHT, 10)
		time_crop_sizer.Add(lbl_end_time, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		time_crop_sizer.Add(self.txt_end, 1, wx.EXPAND)
		main_sizer.Add(time_crop_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

		main_sizer.Add(self.chk_match_rate, 0, wx.LEFT | wx.BOTTOM, 10)

		# Voices and Tabs section
		voices_tabs_sizer = wx.BoxSizer(wx.HORIZONTAL)

		voices_sizer = wx.BoxSizer(wx.VERTICAL)
		voices_sizer.Add(self.lb_voices, 1, wx.EXPAND | wx.RIGHT, 10)
		voices_sizer.Add(btn_new_speaker, 0, wx.TOP, 5)

		voices_tabs_sizer.Add(voices_sizer, 1, wx.EXPAND | wx.ALL, 10)
		voices_tabs_sizer.Add(tab_control, 3, wx.EXPAND | wx.ALL, 10) # Tabs take more space

		main_sizer.Add(voices_tabs_sizer, 1, wx.EXPAND)

		# Run dubbing button
		run_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
		run_button_sizer.AddStretchSpacer(1)
		run_button_sizer.Add(btn_run_dub, 0, wx.ALL, 10)
		main_sizer.Add(run_button_sizer, 0, wx.EXPAND | wx.BOTTOM | wx.RIGHT, 5)

		self.tab_voice_config.update_voice_fields(None)
		self.SetSizerAndFit(main_sizer)
		wx.CallAfter(self.check_ffmpeg)

	def check_ffmpeg(self):
		if not feature_support.ffmpeg_supported:
			msg_has_ffmpeg = wx.MessageDialog(self, "FFmpeg is not detected on your system, Would you like to automatically install it?", "Install FFmpeg?", style=wx.YES_NO | wx.ICON_QUESTION)
			if msg_has_ffmpeg.ShowModal() == wx.ID_YES:
				msg_loading = wx.ProgressDialog("Installing FFmpeg...", "Installing FFmpeg", parent=self, style=wx.PD_AUTO_HIDE | wx.PD_SMOOTH)
				msg_loading.Update(1)
				try:
					feature_support.install_ffmpeg()
				except Exception as e:
					print(e)
					wx.MessageBox(f"Installing FFmpeg failed, please install it manually, and add it to your system envionrment path.\n\n{e}", "FFmpeg Install failed", wx.ICON_ERROR, self)
				msg_loading.Destroy()
  

	def open_file(self, evenet):
		dlg = wx.FileDialog(
			frame, message="Choose a file",
			wildcard="*.*",
			style=wx.FD_OPEN | wx.FD_CHANGE_DIR
		)
		if dlg.ShowModal() == wx.ID_OK:
			self.load_video(dlg.GetPath())
		dlg.Destroy()

	def load_video(self, video_path):
		def update_ui():
			self.txt_main_file.Value = app_state.video.file
			self.txt_start.SetValue(utils.seconds_to_timecode(app_state.video.start_time))
			self.txt_end.SetValue(utils.seconds_to_timecode(app_state.video.end_time))
			self.tab_subtitles.create_entries()

		def initialize_video(progress=True):
			app_state.video = Video(video_path, update_progress if progress else print, lang=self.txt_dl_lang.Value)
			wx.CallAfter(update_ui)
			wx.CallAfter(self.streams_tab.populate_streams, app_state.video.list_streams())

		if video_path.startswith("http"):
			dialog = wx.ProgressDialog("Downloading Video", "Download starting", 100, self)

			def update_progress(progress=None):
				status = progress['status'] if progress else "waiting"
				total = progress.get("fragment_count", progress.get("total_bytes", 0))
				if status == "downloading" and total:
					completed = progress.get("fragment_index", progress.get("downloaded_bytes", 1))
					percent_complete = int(100 * (completed / total))
					wx.CallAfter(dialog.Update, percent_complete, f"{status}: {percent_complete}% \n {progress['info_dict'].get('fulltitle', '')}")
				elif status == "complete":
					if dialog:
						wx.CallAfter(dialog.Destroy)
				elif status == "error":
					wx.CallAfter(wx.MessageBox,
						f"Failed to download video with the following Error:\n {str(progress['error'])}",
						"Error",
						wx.ICON_ERROR
					)
					update_progress({"status": "complete"})

			threading.Thread(target=initialize_video).start()
		else:
			initialize_video(False)

	def change_crop_time(self, event):
		app_state.video.update_time(
			utils.timecode_to_seconds(self.txt_start.Value),
			utils.timecode_to_seconds(self.txt_end.Value)
		)
		self.tab_subtitles.create_entries()

	def update_voices_list(self):
		self.lb_voices.Set([speaker.name for speaker in app_state.speakers])
		self.lb_voices.Select(self.lb_voices.Strings.index(app_state.current_speaker.name))

	def on_voice_change(self, event):
		app_state.current_speaker = app_state.speakers[self.lb_voices.GetSelection()]
		app_state.sample_speaker = app_state.current_speaker
		self.tab_voice_config.update_voice_fields(event)

	def add_speaker(self, event):
		num_voice = self.lb_voices.GetCount()
		app_state.speakers.append(Voice(Voice.VoiceType.SYSTEM, name=f"Voice {num_voice}"))
		self.update_voices_list()
		self.lb_voices.Select(num_voice)

	def run_dub(self, event):
		progress_dialog = wx.ProgressDialog(
			"Dubbing Progress",
			"Starting...",
			maximum=len(app_state.video.subs_adjusted) + 1,  # +1 for combining phase
			parent=self,
			style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE
		)
		dub_thread = None
		def update_progress(i, text=""):
			if i == -1:
				return wx.CallAfter(progress_dialog.Destroy)
			wx.CallAfter(progress_dialog.Update, i, text)

		dub_thread = threading.Thread(target=app_state.video.run_dubbing, args=(update_progress,self.chk_match_rate.GetValue()))
		dub_thread.start()

if __name__ == '__main__':
	utils.create_output_dir()
	app = wx.App(False)
	frame = wx.Frame(None, wx.ID_ANY, utils.APP_NAME, size=(1270, 800))
	frame.Center()
	icon_path = "logo.ico" if not utils.is_deployed else os.path.join('_internal', 'logo.ico')
	frame.SetIcon(wx.Icon(os.path.abspath(icon_path), wx.BITMAP_TYPE_ANY))
	gui = GUI(frame)
	frame.Show()
	app.MainLoop()
