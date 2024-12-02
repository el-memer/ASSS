import gi
import os
from subprocess import Popen, call
from signal import SIGTERM

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


class SoundPlayer:
    def __init__(self, file, time=""):
        self.sound_file = file
        self.time = time

    def play(self):
        self.time2 = 0
        if override.get_active():
            self.time2 = start_time.get_value()
        elif self.time:
            self.time2 = float(self.time) / 10

        freqs_mplayer = ":".join(str(freq.get_value()) for freq in freqs)
        self.sound_process = Popen(
            ["mplayer", "-ss", str(self.time2), "-af", f"equalizer={freqs_mplayer}", self.sound_file]
        )

    def stop(self):
        os.kill(self.sound_process.pid, SIGTERM)


class SamplerButton(Gtk.ToggleButton):
    def __init__(self, file=""):
        filename = os.path.basename(file)
        name, ext = os.path.splitext(filename)
        parts = name.split("#")
        label = parts[0].capitalize()[:15]
        time = parts[1] if len(parts) == 2 else ""
        super().__init__(label=label)
        self.sound = SoundPlayer(file, time)
        self.file = file
        self.connect("toggled", self.toggle)

    def toggle(self, widget):
        if self.get_active():
            self.sound.play()
            current_song_label.set_text(f"Playing: {os.path.basename(self.file)}")
        else:
            self.sound.stop()
            current_song_label.set_text("")


class Sampler(Gtk.ApplicationWindow):
    def __init__(self, **kargs):

        super().__init__(**kargs, title='Simple sampler')
        self.set_default_size(800, 600)

        main_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_child(main_panel)

        # Equalizer
        equalizer_box = Gtk.Box(spacing=10, height_request= 100)
        init_eq_button = Gtk.Button(label="Init EQ")
        init_eq_button.connect("clicked", self.equalizer_init)
        equalizer_box.append(init_eq_button)

        global freqs
        freqs = [
            Gtk.Scale.new_with_range(Gtk.Orientation.VERTICAL, -10, 10, 0.1)
            for _ in range(10)
        ]
        for scale in freqs:
            scale.set_value(0)
            scale.set_inverted(True)
            equalizer_box.append(scale)

        main_panel.append(equalizer_box)

        # Current song display
        global current_song_label
        current_song_label = Gtk.Label(label="")
        current_song_label.set_halign(Gtk.Align.END)
        main_panel.append(current_song_label)

        # Notebook with horizontal scrollbar
        notebook_scrolled = Gtk.ScrolledWindow()
        notebook_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)

        notebook = Gtk.Notebook(height_request=300)
        notebook_scrolled.set_child(notebook)
        main_panel.append(notebook_scrolled)

        sounds_dir = "sounds"
        for directory in sorted(os.listdir(sounds_dir)):
            tab_label = Gtk.Label(label=directory)
            scrolled_tab_content = Gtk.ScrolledWindow()
            scrolled_tab_content.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            tab_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

            for subdir in sorted(os.listdir(os.path.join(sounds_dir, directory))):
                subdir_path = os.path.join(sounds_dir, directory, subdir)

                subdir_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                subdir_label = Gtk.Label(label=subdir)
                subdir_box.append(subdir_label)

                # Limit to 10 songs and add "Show More" button if needed
                songs = sorted(os.listdir(subdir_path))
                for idx, sound in enumerate(songs[:10]):
                    sound_path = os.path.join(subdir_path, sound)
                    subdir_box.append(SamplerButton(sound_path))

                if len(songs) > 10:
                    show_more_button = Gtk.Button(label="Show More")
                    show_more_button.connect("clicked", self.show_more, subdir_box, songs[10:], subdir_path)
                    subdir_box.append(show_more_button)

                tab_content.append(subdir_box)

            scrolled_tab_content.set_child(tab_content)
            notebook.append_page(scrolled_tab_content, tab_label)

        # Side panel
        side_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        volume_label = Gtk.Label(label="Volume")
        side_panel.append(volume_label)

        global start_time, override
        start_time = Gtk.SpinButton.new_with_range(0, 200, 0.1)
        override = Gtk.CheckButton(label="Override Start Time")
        side_panel.append(start_time)
        side_panel.append(override)

        volume_scale = Gtk.Scale.new_with_range(Gtk.Orientation.VERTICAL, 0, 100, 1)
        volume_scale.set_value(75)
        volume_scale.set_inverted(True)
        volume_scale.connect("value-changed", self.set_volume)
        side_panel.append(volume_scale)

        main_panel.append(side_panel)

    def equalizer_init(self, widget):
        for scale in freqs:
            scale.set_value(0)

    def set_volume(self, scale):
        volume = scale.get_value()
        call(["amixer", "set", "Master", f"{int(volume)}%"])

    def show_more(self, button, subdir_box, remaining_songs, subdir_path):
        button.set_visible(False)
        for sound in remaining_songs:
            sound_path = os.path.join(subdir_path, sound)
            subdir_box.append(SamplerButton(sound_path))

def on_activate(app):

    # Create window

    win = Sampler(application=app )

    win.present()

def main():
    app = Gtk.Application(application_id='com.example.App')
    app.connect('activate', on_activate)

    app.run(None)



if __name__ == "__main__":
    main()
