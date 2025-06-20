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

		# --- Google Cloud TTS Specific Controls ---
		self.lbl_gcloud_language = wx.StaticText(self, label="Google Cloud Language")
		self.cb_gcloud_language = wx.Choice(self, choices=[])
		self.cb_gcloud_language.Bind(wx.EVT_CHOICE, self.on_gcloud_language_change)
		self.gcloud_lang_sizer_item = self.add_control_with_label(grid_sizer, self.lbl_gcloud_language, self.cb_gcloud_language, style_widget, return_sizer_item=True)

		self.lbl_gcloud_voice = wx.StaticText(self, label="Google Cloud Voice")
		self.cb_gcloud_voice = wx.Choice(self, choices=[])
		self.cb_gcloud_voice.Bind(wx.EVT_CHOICE, self.on_gcloud_voice_change)
		self.gcloud_voice_sizer_item = self.add_control_with_label(grid_sizer, self.lbl_gcloud_voice, self.cb_gcloud_voice, style_widget, return_sizer_item=True)

		self.lbl_gcloud_speaking_rate = wx.StaticText(self, label="Speaking Rate (0.25-4.0)")
		self.slider_gcloud_speaking_rate = wx.Slider(self, value=100, minValue=25, maxValue=400) # Represent 1.00 as 100
		self.slider_gcloud_speaking_rate.Bind(wx.EVT_SLIDER, self.on_gcloud_params_change)
		self.gcloud_rate_sizer_item = self.add_control_with_label(grid_sizer, self.lbl_gcloud_speaking_rate, self.slider_gcloud_speaking_rate, style_widget, return_sizer_item=True)

		self.lbl_gcloud_pitch = wx.StaticText(self, label="Pitch (-20.0 to 20.0)")
		self.slider_gcloud_pitch = wx.Slider(self, value=0, minValue=-200, maxValue=200) # Represent 0.0 as 0, scale by 10
		self.slider_gcloud_pitch.Bind(wx.EVT_SLIDER, self.on_gcloud_params_change)
		self.gcloud_pitch_sizer_item = self.add_control_with_label(grid_sizer, self.lbl_gcloud_pitch, self.slider_gcloud_pitch, style_widget, return_sizer_item=True)

		# Initially hide Google Cloud controls
		self.show_google_cloud_options(False, grid_sizer)


	def add_control_with_label(self, sizer, label, control, style_func, control_is_checkbox=False, return_sizer_item=False):
		style_func(label)
		style_func(control, is_input=True)

		# For checkboxes, the label is part of the control. Add a spacer for the label column.
		label_sizer_item = None
		control_sizer_item = None
		if control_is_checkbox:
			# For checkboxes, the control itself (which includes the label) takes the first slot,
			# and we might add a dummy spacer or just let it span if the sizer is configured for it.
			# Here, we assume FlexGridSizer handles columns based on additions.
			control_sizer_item = sizer.Add(control, 0, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND, 5)
			label_sizer_item = sizer.Add(wx.StaticText(self, label=""), 0) # Placeholder for the "label" column if needed
		else:
			label_sizer_item = sizer.Add(label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
			control_sizer_item = sizer.Add(control, 1, wx.ALL | wx.EXPAND, 5) # Control takes proportion 1 to expand

		if return_sizer_item:
			return label_sizer_item, control_sizer_item
		# else:
			# return None # Or don't return anything explicitly

	def show_google_cloud_options(self, show, sizer):
		# Helper to show/hide a sizer item (label and control pair)
		def show_hide_item_pair(label_item, control_item, show_flag):
			if label_item and control_item:
				label_widget = label_item.GetWindow()
				control_widget = control_item.GetWindow()
				if label_widget: label_widget.Show(show_flag)
				if control_widget: control_widget.Show(show_flag)
				label_item.Show(show_flag)
				control_item.Show(show_flag)

		show_hide_item_pair(self.gcloud_lang_sizer_item[0], self.gcloud_lang_sizer_item[1], show)
		show_hide_item_pair(self.gcloud_voice_sizer_item[0], self.gcloud_voice_sizer_item[1], show)
		show_hide_item_pair(self.gcloud_rate_sizer_item[0], self.gcloud_rate_sizer_item[1], show)
		show_hide_item_pair(self.gcloud_pitch_sizer_item[0], self.gcloud_pitch_sizer_item[1], show)

		# Hide Coqui-specific controls if showing Google Cloud, and vice-versa
		# Assuming Coqui controls are always present in the sizer and just shown/hidden
		self.lbl_coqui_lang.Show(not show and app_state.sample_speaker.voice_type == Voice.VoiceType.COQUI)
		self.cb_coqui_lang.Show(not show and app_state.sample_speaker.voice_type == Voice.VoiceType.COQUI)
		self.chk_speaker_wav.Show(not show and app_state.sample_speaker.voice_type == Voice.VoiceType.COQUI)
		self.file_speaker_wav.Show(not show and app_state.sample_speaker.voice_type == Voice.VoiceType.COQUI)
		self.lbl_speaker_voices.Show(not show and app_state.sample_speaker.voice_type == Voice.VoiceType.COQUI and app_state.sample_speaker.is_multispeaker)
		self.cb_speaker_voices.Show(not show and app_state.sample_speaker.voice_type == Voice.VoiceType.COQUI and app_state.sample_speaker.is_multispeaker)

		self.Layout()


	def sample(self, event):
		utils.sampleVoice(self.txt_sample_text.Value)

	# When the user clicks update voice, asign one in the array to the specification
	def update_voice(self, event):
		app_state.sample_speaker.name = self.txt_voice_name.Value
		app_state.speakers[app_state.speakers.index(app_state.current_speaker)] = app_state.sample_speaker
		app_state.current_speaker = app_state.sample_speaker
		self.parent.update_voices_list()

	# determines weather to show hidden models based on the state of the selected voice model/engine
	def show_hidden_options(self):
		# Hide all optional sections first
		self.lbl_coqui_lang.Hide()
		self.cb_coqui_lang.Hide()
		self.chk_speaker_wav.Hide()
		self.file_speaker_wav.Hide()
		self.lbl_speaker_voices.Hide()
		self.cb_speaker_voices.Hide()
		self.btn_patch_onecore.Hide()
		self.show_google_cloud_options(False, self.GetSizer()) # Pass the main sizer

		# Show options based on current voice type
		voice_type = app_state.sample_speaker.voice_type
		if voice_type == Voice.VoiceType.COQUI:
			self.lbl_coqui_lang.Show()
			self.cb_coqui_lang.Show()
			self.cb_coqui_lang.Set(list(app_state.sample_speaker.langs))
			self.cb_coqui_lang.Select(app_state.sample_speaker.langs.index(app_state.sample_speaker.selected_lang))
			self.chk_speaker_wav.Show()
			self.file_speaker_wav.Show()
			self.chk_speaker_wav.SetValue(app_state.sample_speaker.use_vc)
			self.file_speaker_wav.SetPath(app_state.sample_speaker.speaker_wav)
			self.change_model_language(None) # To update model options based on lang
			if app_state.sample_speaker.is_multispeaker:
				self.lbl_speaker_voices.Show()
				self.cb_speaker_voices.Show()
				self.cb_speaker_voices.Set(app_state.sample_speaker.list_speakers())
				if app_state.sample_speaker.speaker:
					self.cb_speaker_voices.SetStringSelection(app_state.sample_speaker.speaker)
		elif voice_type == Voice.VoiceType.SYSTEM and app_state.platform == 'win32':
			self.btn_patch_onecore.Show()
		elif voice_type == Voice.VoiceType.GOOGLE_CLOUD:
			self.show_google_cloud_options(True, self.GetSizer())
			self.populate_gcloud_languages()
			# Initial population of voices for the default language
			self.populate_gcloud_voices(app_state.sample_speaker.selected_language_code)
			# Set sliders to current voice's params
			self.slider_gcloud_speaking_rate.SetValue(int(app_state.sample_speaker.speaking_rate * 100))
			self.slider_gcloud_pitch.SetValue(int(app_state.sample_speaker.pitch * 10))


		self.Layout()

	# Populate the form with the current sample speaker's params
	def update_voice_fields(self, event=None): # Added default for event
		self.txt_voice_name.Value = app_state.sample_speaker.name
		current_engine_index = self.available_engines.index(app_state.sample_speaker.voice_type)
		self.cb_tts_engines.Select(current_engine_index)

		self.show_hidden_options() # This will handle showing/hiding Coqui or Google Cloud options

		if app_state.sample_speaker.voice_type == Voice.VoiceType.GOOGLE_CLOUD:
			# For Google Cloud, "Model Options" isn't directly used in the same way.
			# Language and Voice are separate. We can hide or disable cb_model_options.
			# Or, cb_model_options could list something else if applicable. For now, hide.
			self.cb_model_options.Hide() # Hide generic model options for GCloud
			# Ensure GCloud specific dropdowns are populated and set
			self.populate_gcloud_languages()
			if app_state.sample_speaker.selected_language_code:
					self.cb_gcloud_language.SetStringSelection(app_state.sample_speaker.selected_language_code)
					self.populate_gcloud_voices(app_state.sample_speaker.selected_language_code)
					if app_state.sample_speaker.selected_voice_name:
							self.cb_gcloud_voice.SetStringSelection(app_state.sample_speaker.selected_voice_name)
			self.slider_gcloud_speaking_rate.SetValue(int(app_state.sample_speaker.speaking_rate * 100))
			self.slider_gcloud_pitch.SetValue(int(app_state.sample_speaker.pitch * 10))

		else: # For Coqui, System, ESpeak
			self.cb_model_options.Show()
			options = app_state.sample_speaker.list_voice_options()
			self.cb_model_options.Set(options if options else [])
			try:
				if app_state.sample_speaker.voice_option and options:
					self.cb_model_options.Select(options.index(app_state.sample_speaker.voice_option))
				elif options:
					self.cb_model_options.Select(0)
			except ValueError: # voice_option not in list
				if options: self.cb_model_options.Select(0)
		self.Layout()


	def change_tts_engine(self, event):
		selected_engine_type = self.available_engines[self.cb_tts_engines.GetSelection()]
		# Only create a new Voice object if the type actually changes
		if not isinstance(app_state.sample_speaker, selected_engine_type.value[0]): # This check is a bit complex due to VoiceType storing tuple
			app_state.sample_speaker = Voice(selected_engine_type)
		self.update_voice_fields(event)

	# Update the sample speaker to the specification
	def change_voice_params(self, event): # Generic handler for Coqui/System/ESpeak model options
		if app_state.sample_speaker.voice_type == Voice.VoiceType.GOOGLE_CLOUD:
			# This event is for cb_model_options, which should be hidden for GCloud.
			# GCloud params are handled by their own dedicated handlers (on_gcloud_language_change, etc.)
			return

		self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
		self.Layout() # Ensure UI updates before potentially long operation

		option_name = self.cb_model_options.GetStringSelection()
		
		# Coqui-specific download and parameter setting logic
		if app_state.sample_speaker.voice_type == Voice.VoiceType.COQUI:
			def coqui_run_after():
				app_state.sample_speaker.set_voice_params(voice=option_name) # This sets model_name
				app_state.sample_speaker.set_voice_params(speaker_wav=self.file_speaker_wav.GetPath())
				if app_state.sample_speaker.is_multispeaker:
					app_state.sample_speaker.set_voice_params(speaker=self.cb_speaker_voices.GetStringSelection())
				app_state.sample_speaker.set_voice_params(use_vc=self.chk_speaker_wav.IsChecked())
				self.update_voice_fields(event) # Refresh UI based on new params
				self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))

			if not app_state.sample_speaker.is_model_downloaded(option_name):
				# ... (Coqui download dialog logic remains the same)
				message_download = wx.MessageDialog(
					None,
					f"You do not have\n{option_name}\n downloaded. Would you like to download it? It could take a long time and lots of storage",
					"Download this model?",
					wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION
				).ShowModal()
				if(message_download != wx.ID_YES):
					self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))
					return

				dialog_download = wx.ProgressDialog("Downloading Model", "Starting...", 100, self)
				dialog_download.Pulse("Connecting...")

				def download_progress(progress_val, status=None): # Renamed progress to progress_val to avoid conflict
					if progress_val == -1: # Indicates completion or error from Voice.py
						wx.CallAfter(dialog_download.Destroy)
						wx.CallAfter(coqui_run_after)
						return
					wx.CallAfter(dialog_download.Update, progress_val, f"{progress_val}% - {status} \n {option_name}")

				# Corrected kwargs to use 'progress' as expected by CoquiVoice.set_voice_params
				threading.Thread(target=app_state.sample_speaker.set_voice_params, kwargs={"voice": option_name, "progress": download_progress}).start()
			else: # Model already downloaded
				coqui_run_after()
		else: # For System or ESpeak voices
			app_state.sample_speaker.set_voice_params(voice=option_name)
			self.update_voice_fields(event) # Refresh UI
			self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))

	def on_gcloud_language_change(self, event):
		if not app_state.sample_speaker.voice_type == Voice.VoiceType.GOOGLE_CLOUD: return
		selected_lang = self.cb_gcloud_language.GetStringSelection()
		app_state.sample_speaker.set_voice_params(language_code=selected_lang)
		self.populate_gcloud_voices(selected_lang)
		# Auto-select the first voice for the new language or current if still valid
		voices = self.cb_gcloud_voice.GetStrings()
		if voices:
			current_gcloud_voice = app_state.sample_speaker.selected_voice_name
			if current_gcloud_voice in voices:
				self.cb_gcloud_voice.SetStringSelection(current_gcloud_voice)
			else:
				self.cb_gcloud_voice.SetSelection(0)
				app_state.sample_speaker.set_voice_params(voice_name=self.cb_gcloud_voice.GetStringSelection())
		else: # No voices for this language? Clear selection
			app_state.sample_speaker.set_voice_params(voice_name=None)


	def on_gcloud_voice_change(self, event):
		if not app_state.sample_speaker.voice_type == Voice.VoiceType.GOOGLE_CLOUD: return
		selected_voice = self.cb_gcloud_voice.GetStringSelection()
		app_state.sample_speaker.set_voice_params(voice_name=selected_voice)

	def on_gcloud_params_change(self, event): # For sliders
		if not app_state.sample_speaker.voice_type == Voice.VoiceType.GOOGLE_CLOUD: return
		rate = self.slider_gcloud_speaking_rate.GetValue() / 100.0
		pitch = self.slider_gcloud_pitch.GetValue() / 10.0
		app_state.sample_speaker.set_voice_params(speaking_rate=rate, pitch=pitch)

	def populate_gcloud_languages(self):
		if not app_state.sample_speaker.voice_type == Voice.VoiceType.GOOGLE_CLOUD: return
		try:
			langs = app_state.sample_speaker.list_languages()
			self.cb_gcloud_language.SetItems(langs if langs else ["N/A"])
			if app_state.sample_speaker.selected_language_code in langs:
				self.cb_gcloud_language.SetStringSelection(app_state.sample_speaker.selected_language_code)
			elif langs:
				self.cb_gcloud_language.SetSelection(0)
		except Exception as e:
			print(f"Error populating Google Cloud languages: {e}")
			self.cb_gcloud_language.SetItems(["Error loading"])
			self.cb_gcloud_language.SetSelection(0)

	def populate_gcloud_voices(self, language_code):
		if not app_state.sample_speaker.voice_type == Voice.VoiceType.GOOGLE_CLOUD: return
		try:
			# voice_objects is a list of Google's Voice objects
			voice_objects = app_state.sample_speaker.list_voice_options(language_code=language_code)
			voice_names = [v.name for v in voice_objects]
			self.cb_gcloud_voice.SetItems(voice_names if voice_names else ["N/A"])

			if app_state.sample_speaker.selected_voice_name in voice_names:
				self.cb_gcloud_voice.SetStringSelection(app_state.sample_speaker.selected_voice_name)
			elif voice_names: # If current selection invalid, pick first available
				self.cb_gcloud_voice.SetSelection(0)
				# Update the actual speaker voice if we auto-selected
				app_state.sample_speaker.set_voice_params(voice_name=self.cb_gcloud_voice.GetStringSelection())
		except Exception as e:
			print(f"Error populating Google Cloud voices for {language_code}: {e}")
			self.cb_gcloud_voice.SetItems(["Error loading"])
			self.cb_gcloud_voice.SetSelection(0)
			

	def change_model_language(self, event): # Coqui-specific
		if not app_state.sample_speaker.voice_type == Voice.VoiceType.COQUI: return
		if self.cb_coqui_lang.GetSelection() == 0: # If they have "All Voices" selected, don't filter
			self.cb_model_options.Set(app_state.sample_speaker.list_voice_options())
		else:
			self.cb_model_options.Set([model for model in app_state.sample_speaker.list_voice_options() if f"/{self.cb_coqui_lang.GetStringSelection()}/" in model])
			app_state.sample_speaker.selected_lang = self.cb_coqui_lang.GetStringSelection()
		# Attempt to reselect previous model or first if not available
		current_model = app_state.sample_speaker.voice_option
		new_options = self.cb_model_options.GetStrings()
		if current_model in new_options:
			self.cb_model_options.SetStringSelection(current_model)
		elif new_options:
			self.cb_model_options.Select(0)


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
