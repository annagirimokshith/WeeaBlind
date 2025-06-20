import wx
import app_state
import vocal_isolation
import dub_line
import re
import feature_support
from pydub import AudioSegment
from pydub.playback import play
import utils

if feature_support.ocr_supported:
	import video_ocr
if feature_support.nostril_supported:
	from nostril import nonsense

class ListStreamsTab(wx.Panel):
	def __init__(self, parent, context, colors=None, fonts=None): # Added colors and fonts
		super().__init__(parent)
		
		self.context = context
		self.colors = colors if colors else {
			"background": wx.Colour(240, 240, 240), "text": wx.Colour(50, 50, 50),
			"accent": wx.Colour(0, 120, 215), "input_bg": wx.Colour(255,255,255)
		}
		self.fonts = fonts if fonts else {
			"label": wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL),
			"input": wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL),
			"button": wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		}
		self.SetBackgroundColour(self.colors["background"])

		# --- Main Sizer ---
		main_sizer = wx.BoxSizer(wx.VERTICAL)

		# --- Actions Box (Remove Vocals, OCR) ---
		actions_box = wx.StaticBox(self, label="Advanced Stream Actions")
		actions_box.SetFont(self.fonts["label"])
		actions_box.SetForegroundColour(self.colors["text"])
		actions_sizer = wx.StaticBoxSizer(actions_box, wx.HORIZONTAL)

		btn_remove_vocals = wx.Button(self, label="Remove Vocals from Source")
		btn_remove_vocals.SetFont(self.fonts["button"])
		btn_remove_vocals.Bind(wx.EVT_BUTTON, self.remove_vocals)
		if not feature_support.vocal_isolation_supported: btn_remove_vocals.Disable()
		actions_sizer.Add(btn_remove_vocals, 0, wx.RIGHT, 10)

		btn_ocr = wx.Button(self, label="Extract Subs with OCR")
		btn_ocr.SetFont(self.fonts["button"])
		btn_ocr.Bind(wx.EVT_BUTTON, self.run_ocr)
		if not feature_support.ocr_supported: btn_ocr.Disable()
		actions_sizer.Add(btn_ocr, 0)
		main_sizer.Add(actions_sizer, 0, wx.EXPAND | wx.ALL, 10)

		# --- Scroll Panel for Stream Selection ---
		self.scroll_panel = wx.ScrolledWindow(self, style=wx.VSCROLL)
		self.scroll_panel.SetBackgroundColour(self.colors["background"])
		self.scroll_sizer = wx.BoxSizer(wx.VERTICAL) # Sizer for content INSIDE scroll_panel
		self.scroll_panel.SetSizer(self.scroll_sizer)
		self.scroll_panel.SetScrollRate(0, 20)

		# Audio Streams
		lbl_audio_streams = wx.StaticText(self.scroll_panel, label="Select an Audio Stream:")
		lbl_audio_streams.SetFont(self.fonts["label"])
		lbl_audio_streams.SetForegroundColour(self.colors["text"])
		self.scroll_sizer.Add(lbl_audio_streams, 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)
		self.rb_audio = wx.RadioBox(self.scroll_panel, majorDimension=1, style=wx.RA_SPECIFY_COLS)
		self.rb_audio.SetFont(self.fonts["input"]) # Radiobox items font
		self.scroll_sizer.Add(self.rb_audio, 0, wx.EXPAND | wx.ALL, 10)

		# Subtitle Streams
		lbl_subtitle_streams = wx.StaticText(self.scroll_panel, label="Select a Subtitle Stream:")
		lbl_subtitle_streams.SetFont(self.fonts["label"])
		lbl_subtitle_streams.SetForegroundColour(self.colors["text"])
		self.scroll_sizer.Add(lbl_subtitle_streams, 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)
		self.rb_subs = wx.RadioBox(self.scroll_panel, majorDimension=1, style=wx.RA_SPECIFY_COLS)
		self.rb_subs.SetFont(self.fonts["input"])
		self.scroll_sizer.Add(self.rb_subs, 0, wx.EXPAND | wx.ALL, 10)

		# Import External Subtitles
		lbl_import_external = wx.StaticText(self.scroll_panel, label="Import External Subtitles File:")
		lbl_import_external.SetFont(self.fonts["label"])
		lbl_import_external.SetForegroundColour(self.colors["text"])
		self.scroll_sizer.Add(lbl_import_external, 0, wx.TOP | wx.LEFT | wx.RIGHT, 10)
		self.file_import_external = wx.FilePickerCtrl(self.scroll_panel, message="Import External subtitles file", wildcard="Subtitle Files |*.srt;*.vtt;*.ass")
		# FilePickerCtrl often uses native styling, direct font/color changes might not always apply perfectly
		self.file_import_external.Bind(wx.EVT_FILEPICKER_CHANGED, self.import_subs)
		self.scroll_sizer.Add(self.file_import_external, 0, wx.EXPAND | wx.ALL, 10)

		main_sizer.Add(self.scroll_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

		# --- Audio Mixing Box ---
		box_mixing = wx.StaticBox(self, label="Audio Mixing Settings")
		box_mixing.SetFont(self.fonts["label"])
		box_mixing.SetForegroundColour(self.colors["text"])
		box_mixing_sizer = wx.StaticBoxSizer(box_mixing, wx.VERTICAL) # Changed to vertical for better layout

		mixing_grid_sizer = wx.FlexGridSizer(cols=2, vgap=5, hgap=5)
		mixing_grid_sizer.AddGrowableCol(1,1)

		lbl_mixing_ratio = wx.StaticText(self, label="Original Audio / Dub Volume Ratio:")
		lbl_mixing_ratio.SetFont(self.fonts["label"])
		lbl_mixing_ratio.SetForegroundColour(self.colors["text"])
		mixing_grid_sizer.Add(lbl_mixing_ratio, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		self.slider_audio_ratio = wx.Slider(self, value=50) # Min/Max/Initial are default 0-100-0
		self.slider_audio_ratio.Bind(wx.EVT_SLIDER, self.change_mix)
		mixing_grid_sizer.Add(self.slider_audio_ratio, 1, wx.EXPAND)
		box_mixing_sizer.Add(mixing_grid_sizer, 1, wx.EXPAND | wx.BOTTOM, 10)

		mixing_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
		btn_sample_mix = wx.Button(self, label="Preview Mix")
		btn_sample_mix.SetFont(self.fonts["button"])
		btn_sample_mix.Bind(wx.EVT_BUTTON, self.sample_mix)
		mixing_buttons_sizer.Add(btn_sample_mix, 0, wx.RIGHT, 10)
		
		btn_remix_audio = wx.Button(self, label="Remix Video Audio Track")
		btn_remix_audio.SetFont(self.fonts["button"])
		btn_remix_audio.SetBackgroundColour(self.colors["accent"])
		btn_remix_audio.SetForegroundColour(wx.WHITE)
		btn_remix_audio.Bind(wx.EVT_BUTTON, self.remix_audio)
		mixing_buttons_sizer.Add(btn_remix_audio, 0)
		box_mixing_sizer.Add(mixing_buttons_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL)
		
		main_sizer.Add(box_mixing_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

		self.SetSizer(main_sizer)
		self.Layout()


	def populate_streams(self, streams):
		audio_choices = [f"Stream #{stream['index']} ({stream.get('tags', {'language': 'unknown'}).get('language', 'unknown')})" for stream in streams["audio"]]
		if not audio_choices: audio_choices = ["No Audio Streams Found"]
		
		# Store current selection if possible
		current_audio_sel = self.rb_audio.GetSelection() if self.rb_audio.GetCount() > 0 else 0

		self.rb_audio.Clear()
		for choice in audio_choices:
			self.rb_audio.Append(choice)
		if current_audio_sel < self.rb_audio.GetCount():
			self.rb_audio.SetSelection(current_audio_sel)
		else:
			self.rb_audio.SetSelection(0)
		self.rb_audio.Bind(wx.EVT_RADIOBOX, lambda a: self.on_audio_selection(None))
		self.rb_audio.SetFont(self.fonts["input"]) # Reapply font after clearing/appending

		subs_choices = [f"Stream #{stream['stream']} ({stream['name']})" for stream in streams["subs"]]
		if not streams["subs"]:
			subs_choices = ["No Subtitle Streams Found"]

		current_subs_sel = self.rb_subs.GetSelection() if self.rb_subs.GetCount() > 0 else 0

		self.rb_subs.Clear()
		for choice in subs_choices:
			self.rb_subs.Append(choice)
		if current_subs_sel < self.rb_subs.GetCount():
			self.rb_subs.SetSelection(current_subs_sel)
		else:
			self.rb_subs.SetSelection(0)
		self.rb_subs.Bind(wx.EVT_RADIOBOX, lambda a: self.on_subtitle_selection(None, streams)) # Pass streams to handler
		self.rb_subs.SetFont(self.fonts["input"])

		self.scroll_panel.SetupScrolling(scrollToTop=False) # Recalculate scrollbars
		self.Layout()


	def on_audio_selection(self, event):
		if self.rb_audio.GetStringSelection() == "No Audio Streams Found": return
		app_state.video.change_audio(self.rb_audio.GetSelection())
		
	def on_subtitle_selection(self, event, streams):
		if self.rb_subs.GetStringSelection() == "No Subtitle Streams Found": return
		app_state.video.change_subs(stream_index=self.rb_subs.GetSelection()) # Original used selection index
		self.context.tab_subtitles.create_entries()
	
	def run_ocr(self, event):
		frames = video_ocr.perform_video_ocr(app_state.video.file, sample_rate=1)
		ocr_subs = []
		for index, frame in enumerate(frames):
			try:
				if sum(not char.isspace() for char in frame.text) > 6 and not nonsense(frame.text):
					ocr_subs.append(dub_line.DubbedLine(frame.ts_second, -1, frame.text, index))
			except Exception as e:
					print(e)
		app_state.video.subs_adjusted = ocr_subs
		self.context.tab_subtitles.create_entries()
	
	def remove_vocals(self, event):
		utils.attempt_long_running_task(lambda: vocal_isolation.seperate_file(app_state.video), self, "Spleeter Seperating Vocals", "Attempting to Seperate Vocals with Spleeter")

	def import_subs(self, event):
		app_state.video.change_subs(external_path=self.file_import_external.GetPath())
		self.context.tab_subtitles.create_entries()

	def change_mix(self, event):
		app_state.video.mixing_ratio = self.slider_audio_ratio.GetValue() / 100

	def sample_mix(self, event):
		play(app_state.video.sample_mixing())

	def remix_audio(self, event):
		app_state.video.mix_av(app_state.video.mixing_ratio)