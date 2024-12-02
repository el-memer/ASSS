import gi
import os
from subprocess import Popen, call
from signal import SIGTERM

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio


class SoundPlayer:
    def __init__(self, file, time = ''):
        self.sound_file = file
        self.sound_process = None
        self.time = time
    def play(self):
        if self.time:
            self.time2 = float(self.time)/10
        else:
            self.time2=0
        if self.sound_process is None:
            self.sound_process = Popen(['mplayer','-ss',str(self.time2), self.sound_file])

    def pause(self):
        if self.sound_process:
            call(["pkill", "-STOP", "-P", str(self.sound_process.pid)])

    def resume(self):
        if self.sound_process:
            call(["pkill", "-CONT", "-P", str(self.sound_process.pid)])

    def stop(self):
        if self.sound_process:
            os.kill(self.sound_process.pid, SIGTERM)
            self.sound_process = None


class PlayedMusicControl(Gtk.Box):
    def __init__(self, player, song_name, remove_callback):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.player = player

        # Song Name
        label = Gtk.Label(label=song_name)
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.START)
        self.append(label)

        # Pause Button
        pause_button = Gtk.Button(label="Pause")
        pause_button.connect("clicked", self.pause_song)
        self.append(pause_button)

        # Resume Button
        resume_button = Gtk.Button(label="Resume")
        resume_button.connect("clicked", self.resume_song)
        self.append(resume_button)

        # Volume Slider
        volume_slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        volume_slider.set_value(75)
        volume_slider.connect("value-changed", self.set_volume)
        self.append(volume_slider)

        # Remove Button
        remove_button = Gtk.Button(label="Remove")
        remove_button.connect("clicked", lambda _: remove_callback(self))
        self.append(remove_button)

    def pause_song(self, _):
        self.player.pause()

    def resume_song(self, _):
        self.player.resume()

    def set_volume(self, slider):
        volume = slider.get_value()
        call(["amixer", "set", "Master", f"{int(volume)}%"])


class SamplerButton(Gtk.ToggleButton):
    def __init__(self, file, played_music_panel):
        super().__init__(label=os.path.basename(file)[:15])
        print(file.split('#'))
        filename_array = file.split('#')
        label = filename_array[0]
        if len(filename_array) >= 2:
            time = filename_array[1]
            print(time)
        else:
            time = ''
        label = label.capitalize()
        label = label[0:15]
        self.sound = SoundPlayer(file, time)
        self.sound_player = SoundPlayer(file, time)
        self.file = file
        self.played_music_panel = played_music_panel
        self.connect("toggled", self.toggle)

    def toggle(self, widget):
        if self.get_active():
            self.sound_player.play()
            self.played_music_panel.add_song(self.sound_player, os.path.basename(self.file))
        else:
            self.sound_player.stop()


class PlayedMusicPanel(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__(height_request=300)
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_child(self.container)

    def add_song(self, player, song_name):
        control = PlayedMusicControl(player, song_name, self.remove_song)
        self.container.append(control)

    def remove_song(self, control):
        control.player.stop()
        self.container.remove(control)


class Sampler(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Simple Sampler")
        self.set_default_size(800, 600)

        main_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_child(main_panel)

        # Bottom Panel for Played Music
        self.played_music_panel = PlayedMusicPanel()

        # Notebook with horizontal scrollbar
        notebook_scrolled = Gtk.ScrolledWindow(height_request=400)
        notebook_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)

        notebook = Gtk.Notebook()
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
                    subdir_box.append(SamplerButton(sound_path, self.played_music_panel))

                if len(songs) > 10:
                    show_more_button = Gtk.Button(label="Show More")
                    show_more_button.connect(
                        "clicked", self.show_more, subdir_box, songs[10:], subdir_path
                    )
                    subdir_box.append(show_more_button)

                tab_content.append(subdir_box)

            scrolled_tab_content.set_child(tab_content)
            notebook.append_page(scrolled_tab_content, tab_label)


        main_panel.append(self.played_music_panel)

    def show_more(self, button, subdir_box, remaining_songs, subdir_path):
        button.set_visible(False)
        for sound in remaining_songs:
            sound_path = os.path.join(subdir_path, sound)
            subdir_box.append(SamplerButton(sound_path, self.played_music_panel))


class SamplerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.example.sampler")

    def do_activate(self):
        window = Sampler(self)
        window.present()


def main():
    app = SamplerApp()
    app.run()


if __name__ == "__main__":
    main()
