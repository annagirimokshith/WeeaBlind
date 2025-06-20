import threading
import app_state
import wx
from Voice import Voice
import utils
import feature_support

class ConfigureVoiceTab(wx.Panel):
	def __init__(self, notebook, parent, colors=None, fonts=None): # Added colors and fonts
		super().__init__(notebook)
		self.parent = parent
		self.colors = colors if colors else {
			"background": wx.Colour(240, 240, 240), "text": wx.Colour(50, 50, 50),
			"accent": wx.Colour(0, 120, 215), "input_bg": wx.Colour(255,255,255)
		}
		self.fonts = fonts if fonts else {
			"label": wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL),
			"input": wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		}
		self.SetBackgroundColour(self.colors["background"])

		# Create a grid sizer with extra padding
		grid_sizer = wx.FlexGridSizer(cols=2, hgap=10, vgap=10) # Increased hgap for better spacing
		grid_sizer.AddGrowableCol(1, 1) # Allow second column to expand

		# Helper function to apply styles
		def style_widget(widget, is_input=False):
			if isinstance(widget, (wx.StaticText, wx.CheckBox)):
				widget.SetFont(self.fonts["label"])
				widget.SetForegroundColour(self.colors["text"])
			elif isinstance(widget, (wx.TextCtrl, wx.Choice, wx.FilePickerCtrl)):
				widget.SetFont(self.fonts["input"])
				if not isinstance(widget, wx.FilePickerCtrl): # FilePickerCtrl styling is more native
					widget.SetBackgroundColour(self.colors.get("input_bg", wx.WHITE))
			elif isinstance(widget, wx.Button):
				widget.SetFont(self.fonts["input"])

		# Add controls with labels
		lbl_voice_name = wx.StaticText(self, label="Name")
		self.txt_voice_name = wx.TextCtrl(self, value=app_state.current_speaker.name)
		self.add_control_with_label(grid_sizer, lbl_voice_name, self.txt_voice_name, style_widget)

		lbl_tts_engines = wx.StaticText(self, label="TTS Engine")
		self.available_engines = [engine for engine in Voice.VoiceType if engine.value[1]]
		self.cb_tts_engines = wx.Choice(self, choices=[engine.value[0] for engine in self.available_engines])
		self.cb_tts_engines.Bind(wx.EVT_CHOICE, self.change_tts_engine)
		self.add_control_with_label(grid_sizer, lbl_tts_engines, self.cb_tts_engines, style_widget)

		self.lbl_coqui_lang = wx.StaticText(self, label="Language")
		self.cb_coqui_lang = wx.Choice(self, choices=[])
		self.cb_coqui_lang.Bind(wx.EVT_CHOICE, self.change_model_language)
		self.add_control_with_label(grid_sizer, self.lbl_coqui_lang, self.cb_coqui_lang, style_widget)
		self.lbl_coqui_lang.Hide()
		self.cb_coqui_lang.Hide()

		lbl_model_options = wx.StaticText(self, label="Model Options")
		self.cb_model_options = wx.Choice(self, choices=app_state.current_speaker.list_voice_options())
		self.cb_model_options.Bind(wx.EVT_CHOICE, self.change_voice_params)
		self.add_control_with_label(grid_sizer, lbl_model_options, self.cb_model_options, style_widget)
		
		self.btn_patch_onecore = wx.Button(self, label="Unlock OneCore Voices (Admin)")
		style_widget(self.btn_patch_onecore)
		self.btn_patch_onecore.Bind(wx.EVT_BUTTON, self.patch_onecore)
		self.btn_patch_onecore.Hide()
		grid_sizer.AddStretchSpacer() # Placeholder for label column
		grid_sizer.Add(self.btn_patch_onecore, 0, wx.ALL | wx.ALIGN_LEFT, 5) # Align left

		self.lbl_speaker_voices = wx.StaticText(self, label="Speaker Voices")
		self.cb_speaker_voices = wx.Choice(self, choices=[])
		self.cb_speaker_voices.Bind(wx.EVT_CHOICE, self.change_voice_params)
		self.add_control_with_label(grid_sizer, self.lbl_speaker_voices, self.cb_speaker_voices, style_widget)
		self.lbl_speaker_voices.Hide()
		self.cb_speaker_voices.Hide()

		self.chk_speaker_wav = wx.CheckBox(self, label="VC / Clone Sample")
		style_widget(self.chk_speaker_wav)
		self.chk_speaker_wav.Bind(wx.EVT_CHECKBOX, self.change_voice_params)
		self.file_speaker_wav = wx.FilePickerCtrl(self, message="Select a voice sample to clone", wildcard="*.wav")
		style_widget(self.file_speaker_wav, is_input=True)
		self.file_speaker_wav.Bind(wx.EVT_FILEPICKER_CHANGED, self.change_voice_params)
		self.add_control_with_label(grid_sizer, self.chk_speaker_wav, self.file_speaker_wav, style_widget, control_is_checkbox=True)

		lbl_sample_text = wx.StaticText(self, label="Sample Text")
		self.txt_sample_text = wx.TextCtrl(self, value="I do be slurpin' that cheese without my momma's permission")
		self.add_control_with_label(grid_sizer, lbl_sample_text, self.txt_sample_text, style_widget)

		# Buttons sizer for bottom buttons
		buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.btn_sample = wx.Button(self, label="▶️ Sample Voice")
		style_widget(self.btn_sample)
		self.btn_sample.Bind(wx.EVT_BUTTON, self.sample)
		buttons_sizer.Add(self.btn_sample, 0, wx.RIGHT, 10) # Add some space between buttons
		
		self.btn_update_voice = wx.Button(self, label="Update Voice")
		style_widget(self.btn_update_voice)
		self.btn_update_voice.SetBackgroundColour(self.colors["accent"])
		self.btn_update_voice.SetForegroundColour(wx.WHITE)
		self.btn_update_voice.Bind(wx.EVT_BUTTON, self.update_voice)
		buttons_sizer.Add(self.btn_update_voice)

		grid_sizer.AddStretchSpacer() # Placeholder for label column
		grid_sizer.Add(buttons_sizer, 0, wx.ALIGN_RIGHT | wx.TOP, 10) # Align buttons to the right

		# Set the grid sizer as the main sizer for the panel with extra padding
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		main_sizer.Add(grid_sizer, 1, wx.ALL | wx.EXPAND, 20) # Increased padding, make grid sizer expand
		self.SetSizerAndFit(main_sizer)

		# Apply styles to initially hidden elements too
		style_widget(self.lbl_coqui_lang)
		style_widget(self.cb_coqui_lang, is_input=True)
		style_widget(self.lbl_speaker_voices)
		style_widget(self.cb_speaker_voices, is_input=True)

	def add_control_with_label(self, sizer, label, control, style_func, control_is_checkbox=False):
		style_func(label)
		style_func(control, is_input=True)

		# For checkboxes, the label is part of the control. Add a spacer for the label column.
		if control_is_checkbox:
			sizer.Add(control, 0, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND, 5) # Checkbox itself contains label
			sizer.Add(wx.StaticText(self, label=""), 0) # Placeholder for the control part if needed or adjust span
		else:
			sizer.Add(label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
			sizer.Add(control, 1, wx.ALL | wx.EXPAND, 5) # Control takes proportion 1 to expand

	def sample(self, event):
		utils.sampleVoice(self.txt_sample_text.Value)

	# When the user clicks update voice, asign one in the array to the specification
	def update_voice(self, event):
		app_state.sample_speaker.name = self.txt_voice_name.Value
		app_state.speakers[app_state.speakers.index(app_state.current_speaker)] = app_state.sample_speaker
		app_state.current_speaker = app_state.sample_speaker
		self.parent.update_voices_list()

	# determines weather to show hidden models based on the state of the selected voice model/engine
	def show_hidden(self):
		if app_state.sample_speaker.voice_type == Voice.VoiceType.COQUI:
				self.lbl_coqui_lang.Show()
				self.cb_coqui_lang.Show()
				self.cb_coqui_lang.Set(list(app_state.sample_speaker.langs))
				self.cb_coqui_lang.Select(app_state.sample_speaker.langs.index(app_state.sample_speaker.selected_lang))
				self.chk_speaker_wav.Show()
				self.file_speaker_wav.Show()
				self.chk_speaker_wav.SetValue(app_state.sample_speaker.use_vc)
				self.file_speaker_wav.SetPath(app_state.sample_speaker.speaker_wav)
				self.change_model_language(None)
				if app_state.sample_speaker.is_multispeaker:
					self.lbl_speaker_voices.Show()
					self.cb_speaker_voices.Show()
					self.cb_speaker_voices.Set(app_state.sample_speaker.list_speakers())
					if app_state.sample_speaker.speaker:
						self.cb_speaker_voices.SetStringSelection(app_state.sample_speaker.speaker)
				else:
					self.lbl_speaker_voices.Hide()
					self.cb_speaker_voices.Hide()
		elif app_state.sample_speaker.voice_type == Voice.VoiceType.SYSTEM and app_state.platform == 'win32':
			self.btn_patch_onecore.Show()
		else:
			self.lbl_coqui_lang.Hide()
			self.cb_coqui_lang.Hide()
			self.chk_speaker_wav.Hide()
			self.file_speaker_wav.Hide()
			self.lbl_speaker_voices.Hide()
			self.cb_speaker_voices.Hide()
			self.btn_patch_onecore.Hide()
		self.Layout()

	# Populate the form with the current sample speaker's params
	def update_voice_fields(self, event):
		self.txt_voice_name.Value = app_state.sample_speaker.name
		self.cb_tts_engines.Select(self.available_engines.index(app_state.sample_speaker.voice_type))

		self.cb_model_options.Set(app_state.sample_speaker.list_voice_options())
		self.show_hidden()
		try:
			self.cb_model_options.Select(self.cb_model_options.GetStrings().index(app_state.sample_speaker.voice_option))
		except:
			self.cb_model_options.Select(0)

	def change_tts_engine(self, event):
		app_state.sample_speaker = Voice(self.available_engines[self.cb_tts_engines.GetSelection()])
		self.update_voice_fields(event)

	# Update the sample speaker to the specification
	def change_voice_params(self, event):
		self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
		self.Layout()
		option_name = self.cb_model_options.GetStringSelection()
		
		def run_after():
			app_state.sample_speaker.set_voice_params(voice=option_name)
			if app_state.sample_speaker.voice_type == Voice.VoiceType.COQUI:
				app_state.sample_speaker.set_voice_params(speaker_wav=self.file_speaker_wav.GetPath())
				if app_state.sample_speaker.is_multispeaker:
					app_state.sample_speaker.set_voice_params(speaker=self.cb_speaker_voices.GetStringSelection())
				app_state.sample_speaker.set_voice_params(use_vc=self.chk_speaker_wav.IsChecked())
				try:
					dialog_download.Destroy()
				except:
					pass
			self.update_voice_fields(event)
			self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))
					
		if app_state.sample_speaker.voice_type == Voice.VoiceType.COQUI:
			if not app_state.sample_speaker.is_model_downloaded(option_name):
				message_download = wx.MessageDialog(
					None,
					f"You do not have\n{option_name}\n downloaded. Would you like to download it? It could take a long time and lots of storage",
					"Downlaod this model?",
					wx.CANCEL
				).ShowModal()
				if(message_download != wx.ID_OK):
					return
				dialog_download = wx.ProgressDialog("Downloading Model", "starting", 100, self)

				def download_progress(progress, status=None):
					if progress == -1:
						wx.CallAfter(run_after)
						return
					wx.CallAfter(dialog_download.Update, progress, f"{progress}% - {status} \n {option_name}")
				threading.Thread(target=app_state.sample_speaker.set_voice_params, kwargs={"voice": option_name, "progress": download_progress}).start()
		wx.CallAfter(run_after)
			

	def change_model_language(self, event):
		if self.cb_coqui_lang.GetSelection() == 0: # If they have "All Voices" selected, don't filter
			self.cb_model_options.Set(app_state.sample_speaker.list_voice_options())
		else:
			self.cb_model_options.Set([model for model in app_state.sample_speaker.list_voice_options() if f"/{self.cb_coqui_lang.GetStringSelection()}/" in model])
			app_state.sample_speaker.selected_lang = self.cb_coqui_lang.GetStringSelection()

	def patch_onecore(self, event):
		msg_prompt_patch = wx.MessageDialog(self, 
"""By default, PyTTSx3 only supports 2 system voices, however, you can add more in
Settings > Time & Language > Speech
To use these voices, you must patch the registry to make them accessible. This requires admin rights and will not impact any other aspect of your system.
Would you like to patch the Windows registry to add these voices?""",
"Add OneCore Voices?",
style=wx.YES_NO)
		if msg_prompt_patch.ShowModal() == wx.ID_YES:
			feature_support.patch_onecore_voices()
