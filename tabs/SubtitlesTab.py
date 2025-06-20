import utils
import app_state
from pydub.playback import play
import wx
import threading
import diarize
import feature_support

class SubtitleEntry(wx.Panel):
	def __init__(self, parent, context, sub, colors=None, fonts=None): # Added colors and fonts
		super().__init__(parent)
		self.text = sub.text
		self.sub = sub
		self.start_time = sub.start
		self.end_time = sub.end
		self.speaker = sub.voice
		self.duration = self.end_time - self.start_time
		self.context = context # This is the main GUI frame
		self.colors = colors
		self.fonts = fonts

		self.SetBackgroundColour(self.colors.get("background_lighter", wx.Colour(250,250,250))) # Slightly lighter for entries

		entry_box_label = f"{utils.seconds_to_timecode(self.start_time)} - {utils.seconds_to_timecode(self.end_time)}"
		entry_box = wx.StaticBox(self, label=entry_box_label)
		entry_box.SetFont(self.fonts["label"])
		entry_box.SetForegroundColour(self.colors["text"])
		
		entry_sizer = wx.StaticBoxSizer(entry_box, wx.HORIZONTAL if self.duration < 10 else wx.VERTICAL) # Horizontal for short subs

		# Text content (Speaker and Text)
		text_content_sizer = wx.BoxSizer(wx.VERTICAL)
		lbl_speaker = wx.StaticText(self, label=f"Speaker: {self.speaker}")
		lbl_speaker.SetFont(self.fonts["label"])
		lbl_speaker.SetForegroundColour(self.colors["text"])
		text_content_sizer.Add(lbl_speaker, 0, wx.BOTTOM, 2)

		lbl_text_val = wx.StaticText(self, label=f"Text: {self.text}")
		lbl_text_val.SetFont(self.fonts["input"]) # Slightly different font for the actual sub text
		lbl_text_val.SetForegroundColour(self.colors["text"])
		lbl_text_val.Wrap(300) # Wrap long subtitles
		text_content_sizer.Add(lbl_text_val, 0, wx.EXPAND)
		entry_sizer.Add(text_content_sizer, 1, wx.EXPAND | wx.ALL, 5)


		# Details and Actions (Language, Buttons, Checkbox)
		details_actions_sizer = wx.BoxSizer(wx.VERTICAL)

		lbl_language = wx.StaticText(self, label=f"Language: {sub.language}")
		lbl_language.SetFont(self.fonts["label"])
		lbl_language.SetForegroundColour(self.colors.get("accent_dark", self.colors["accent"])) # Darker accent for lang
		details_actions_sizer.Add(lbl_language, 0, wx.BOTTOM, 5)

		buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
		btn_playback = wx.Button(self, label="Play Orig.")
		btn_playback.SetFont(self.fonts["input"])
		btn_playback.Bind(wx.EVT_BUTTON, self.on_playback_button_click)
		buttons_sizer.Add(btn_playback, 0, wx.RIGHT, 5)

		btn_sample = wx.Button(self, label="Sample Dub")
		btn_sample.SetFont(self.fonts["input"])
		btn_sample.Bind(wx.EVT_BUTTON, self.on_sample_button_click)
		buttons_sizer.Add(btn_sample, 0)
		details_actions_sizer.Add(buttons_sizer, 0, wx.BOTTOM, 5)

		self.chk_mark_export = wx.CheckBox(self, label="Select")
		self.chk_mark_export.SetFont(self.fonts["label"])
		self.chk_mark_export.SetForegroundColour(self.colors["text"])
		details_actions_sizer.Add(self.chk_mark_export, 0, wx.ALIGN_LEFT)

		entry_sizer.Add(details_actions_sizer, 0, wx.ALL | wx.ALIGN_TOP, 5)

		self.SetSizerAndFit(entry_sizer)

	def on_playback_button_click(self, event):
		play(app_state.video.get_snippet(self.start_time, self.end_time))

	def on_sample_button_click(self, event):
		# Ensure context (main GUI) and its chk_match_rate exist
		match_rate = False
		if hasattr(self.context, 'chk_match_rate') and self.context.chk_match_rate:
			match_rate = self.context.chk_match_rate.GetValue()
		play(self.sub.dub_line_file(match_rate=match_rate)[0])


class SubtitlesTab(wx.Panel):
	def __init__(self, notebook, context, colors=None, fonts=None): # Added colors and fonts
		super().__init__(notebook)
		self.context = context # This is the main GUI frame (GUI instance from weeablind.py)
		self.subs_displayed = []
		self.colors = colors if colors else {
			"background": wx.Colour(240, 240, 240), "text": wx.Colour(50, 50, 50),
			"accent": wx.Colour(0, 120, 215), "input_bg": wx.Colour(255,255,255),
			"background_lighter": wx.Colour(250,250,250)
		}
		self.fonts = fonts if fonts else {
			"label": wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL),
			"input": wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		}
		self.SetBackgroundColour(self.colors["background"])

		# --- Toolbar Replacement with Sizers ---
		controls_sizer = wx.BoxSizer(wx.VERTICAL) # Main sizer for controls area
		
		# Language Filtering Section
		lang_filter_box = wx.StaticBox(self, label="Language Filtering")
		lang_filter_box.SetFont(self.fonts["label"])
		lang_filter_box.SetForegroundColour(self.colors["text"])
		lang_filter_sizer = wx.StaticBoxSizer(lang_filter_box, wx.HORIZONTAL)

		btn_lang_detect = wx.Button(self, label="Detect Languages")
		btn_lang_detect.SetFont(self.fonts["input"])
		btn_lang_detect.Bind(wx.EVT_BUTTON, self.detect_langs)
		lang_filter_sizer.Add(btn_lang_detect, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

		self.lb_detected_langs = wx.CheckListBox(self, choices=[]) # Start empty
		self.lb_detected_langs.SetFont(self.fonts["input"])
		self.lb_detected_langs.SetBackgroundColour(self.colors["input_bg"])
		lang_filter_sizer.Add(self.lb_detected_langs, 1, wx.EXPAND | wx.RIGHT, 5)

		btn_language_filter = wx.Button(self, label="Filter Selected")
		btn_language_filter.SetFont(self.fonts["input"])
		btn_language_filter.Bind(wx.EVT_BUTTON, self.remove_langs)
		lang_filter_sizer.Add(btn_language_filter, 0, wx.ALIGN_CENTER_VERTICAL)
		controls_sizer.Add(lang_filter_sizer, 0, wx.EXPAND | wx.ALL, 10)

		# Actions Section (Diarize, Assign, Export)
		actions_box = wx.StaticBox(self, label="Subtitle Actions")
		actions_box.SetFont(self.fonts["label"])
		actions_box.SetForegroundColour(self.colors["text"])
		actions_sizer = wx.StaticBoxSizer(actions_box, wx.HORIZONTAL)

		btn_diarize = wx.Button(self, label="Run Diarization")
		btn_diarize.SetFont(self.fonts["input"])
		btn_diarize.Bind(wx.EVT_BUTTON, self.run_diarization)
		actions_sizer.Add(btn_diarize, 0, wx.RIGHT, 10)

		btn_assign_to_voice = wx.Button(self, label="Assign Voice to Selected")
		btn_assign_to_voice.SetFont(self.fonts["input"])
		btn_assign_to_voice.Bind(wx.EVT_BUTTON, self.assign_voice)
		actions_sizer.Add(btn_assign_to_voice, 0, wx.RIGHT, 10)

		btn_export_clone = wx.Button(self, label="Export Selected for Clone")
		btn_export_clone.SetFont(self.fonts["input"])
		btn_export_clone.Bind(wx.EVT_BUTTON, self.export_clone)
		actions_sizer.Add(btn_export_clone, 0)
		controls_sizer.Add(actions_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

		# Apply feature support disabling
		if not feature_support.diarization_supported: btn_diarize.Disable()
		if not feature_support.language_detection_supported:
			btn_lang_detect.Disable()
			self.lb_detected_langs.Disable()
			btn_language_filter.Disable()

		# --- Scrollable Panel for Subtitle Entries ---
		self.scroll_panel = wx.ScrolledWindow(self, style=wx.VSCROLL)
		self.scroll_panel.SetBackgroundColour(self.colors["background"])
		self.scroll_sizer = wx.BoxSizer(wx.VERTICAL)
		self.scroll_panel.SetSizer(self.scroll_sizer)
		self.scroll_panel.SetScrollRate(0, 20)

		self.lbl_subs_placecholder = wx.StaticText(self.scroll_panel, label="No Subtitles Loaded. Load a video first.")
		self.lbl_subs_placecholder.SetFont(self.fonts["label"])
		self.lbl_subs_placecholder.SetForegroundColour(self.colors["text"])
		self.scroll_sizer.Add(self.lbl_subs_placecholder, 0, wx.CENTER | wx.ALL, 20)

		# --- Main Sizer for the Tab ---
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		main_sizer.Add(controls_sizer, 0, wx.EXPAND | wx.ALL, 5) # Padding for controls area
		main_sizer.Add(self.scroll_panel, 1, wx.EXPAND | wx.ALL, 5) # Padding for scroll panel
		self.SetSizerAndFit(main_sizer)

	def run_diarization(self, event):
		diarize.run_diarization(app_state.video)
		self.create_entries()
		self.context.update_voices_list()
	
	def detect_langs(self, event):
		dialog = wx.ProgressDialog("Filtering Subtitles", "starting", len(app_state.video.subs_adjusted), self)
		def update_progress(progress, status):
			def run_after():
				self.update_langs()
				self.create_entries()
				dialog.Destroy()
			if progress == -1:
				return wx.CallAfter(run_after)
			else:
				wx.CallAfter(dialog.Update, progress, status)
		threading.Thread(target=app_state.video.detect_subs_lang, args=(update_progress, )).start()

	def filter_language(self, event):
		exclusions = self.lb_detected_langs.CheckedStrings
		print("GWEEP", exclusions)
		app_state.video.filter_multilingual_subtiles(exclusions)
		self.update_langs()
		self.create_entries()


	def create_entries(self):
		self.scroll_sizer.Clear(delete_windows=True)
		if not app_state.video or not app_state.video.subs_adjusted:
			self.lbl_subs_placecholder = wx.StaticText(self.scroll_panel, label="No Subtitles Loaded. Load a video first.")
			self.lbl_subs_placecholder.SetFont(self.fonts["label"])
			self.lbl_subs_placecholder.SetForegroundColour(self.colors["text"])
			self.scroll_sizer.Add(self.lbl_subs_placecholder, 0, wx.CENTER | wx.ALL, 20)
		else:
			for sub in app_state.video.subs_adjusted: # self.subs_displayed:
				subtitle_entry_panel = SubtitleEntry( # Renamed from diarization_entry
					self.scroll_panel,
					context=self.context, # Pass the main GUI frame (GUI instance)
					sub=sub,
					colors=self.colors,    # Pass colors
					fonts=self.fonts       # Pass fonts
				)
				# subtitle_entry_panel.SetRefData # This line seems incomplete/unused, consider removing if not needed
				self.scroll_sizer.Add(subtitle_entry_panel, 0, wx.EXPAND | wx.ALL, border=5)

		self.scroll_panel.Layout() # Layout the scroll_panel to refresh sizer
		self.Layout() # Layout the main tab panel

	def update_langs(self):
		self.lb_detected_langs.Clear()
		self.lb_detected_langs.AppendItems(sorted(list(set(sub.language for sub in app_state.video.subs_adjusted))))
		self.Layout()

	def remove_langs(self, event):
		# maybe move this into the video class?
		app_state.video.subs_adjusted = [sub for sub in app_state.video.subs_adjusted if not sub.language in self.lb_detected_langs.GetCheckedStrings()]
		self.update_langs()
		self.create_entries()
	
	def assign_voice(self, event):
		[child.GetWindow().sub.update_voice(self.context.lb_voices.GetSelection()) for child in self.scroll_sizer.GetChildren() if child.GetWindow().chk_mark_export.IsChecked()],
		self.create_entries()

	def export_clone(self, event):
		dlg_save = wx.FileDialog(self, "Save a new clone sample", "./output", "voice_sample.wav", "*.wav", wx.FD_SAVE)
		if dlg_save.ShowModal() == wx.ID_OK:
			app_state.video.export_clone(
				[child.GetWindow().sub for child in self.scroll_sizer.GetChildren() if child.GetWindow().chk_mark_export.IsChecked()],
				dlg_save.GetPath()
			)
		dlg_save.Destroy()
