"""
Sistema de sonido procedural para Bubble Shooter.
Genera todos los efectos y música usando numpy + pygame.mixer.
No requiere archivos de audio externos.
"""
import numpy as np
import pygame
import random
import math


class SoundManager:
    """Gestiona efectos de sonido y música de fondo generados proceduralmente."""

    def __init__(self):
        # Inicializar mixer con parámetros específicos
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(16)

        self.sample_rate = 44100

        # ── Generar efectos de sonido ──
        self._pop_sounds = [self._generate_pop(i) for i in range(4)]
        self._collision_sound = self._generate_collision()
        self._shoot_sound = self._generate_shoot()
        self._combo_sounds = [self._generate_combo(i) for i in range(3)]
        self._win_sound = self._generate_win_fanfare()
        self._lose_sound = self._generate_lose()
        self._button_hover = self._generate_button_hover()
        self._button_click = self._generate_button_click()

        # ── Música de fondo ──
        self._music_channel = pygame.mixer.Channel(0)
        self._music_playing = False
        self._music_volume = 0.18
        self._music_sound = None
        self._build_background_music()

    # ═══════════════════════════════════════════════════════
    #  GENERADORES DE SONIDO
    # ═══════════════════════════════════════════════════════

    def _make_sound(self, samples_mono):
        """Convierte array mono float64 a Sound de pygame (estéreo 16-bit)."""
        # Normalizar
        peak = np.max(np.abs(samples_mono))
        if peak > 0:
            samples_mono = samples_mono / peak
        # Convertir a 16-bit
        samples_16 = (samples_mono * 32767 * 0.8).astype(np.int16)
        # Estéreo: duplicar canal
        stereo = np.column_stack((samples_16, samples_16))
        return pygame.sndarray.make_sound(stereo)

    def _sine(self, freq, duration, sr=None):
        sr = sr or self.sample_rate
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        return np.sin(2 * np.pi * freq * t)

    def _envelope(self, samples, attack=0.01, decay=0.1, sustain_level=0.6,
                  release=0.2):
        """Envolvente ADSR simple."""
        n = len(samples)
        sr = self.sample_rate
        env = np.ones(n)

        a = int(attack * sr)
        d = int(decay * sr)
        r = int(release * sr)

        for i in range(min(a, n)):
            env[i] = i / max(a, 1)
        for i in range(min(d, n - a)):
            env[a + i] = 1.0 - (1.0 - sustain_level) * (i / max(d, 1))
        if r > 0 and n > r:
            for i in range(r):
                env[n - r + i] = sustain_level * (1 - i / r)

        return samples * env

    # ─── Pop (burbuja explota) ───────────────────────────
    def _generate_pop(self, variant=0):
        """Sonido de pop suave y satisfactorio."""
        sr = self.sample_rate
        dur = 0.15
        n = int(sr * dur)
        t = np.linspace(0, dur, n, endpoint=False)

        # Frecuencia base varía con la variante
        base_freq = 600 + variant * 80
        # Sweep descendente
        freq = base_freq * np.exp(-t * 15)
        phase = np.cumsum(freq) / sr
        wave = np.sin(2 * np.pi * phase) * 0.6

        # Ruido suave para textura
        noise = np.random.randn(n) * 0.15
        noise_env = np.exp(-t * 40)
        wave += noise * noise_env

        # Envolvente rápida
        env = np.exp(-t * 25)
        wave *= env

        sound = self._make_sound(wave)
        sound.set_volume(0.35)
        return sound

    # ─── Colisión (burbuja se adhiere) ───────────────────
    def _generate_collision(self):
        """Sonido de impacto suave al adherirse."""
        sr = self.sample_rate
        dur = 0.12
        n = int(sr * dur)
        t = np.linspace(0, dur, n, endpoint=False)

        # Tono bajo con descenso
        freq = 300 * np.exp(-t * 8)
        phase = np.cumsum(freq) / sr
        wave = np.sin(2 * np.pi * phase) * 0.5

        # Click inicial
        click = np.zeros(n)
        click_len = int(0.005 * sr)
        click[:click_len] = np.sin(2 * np.pi * 1200 * t[:click_len]) * 0.8

        wave += click * np.exp(-t * 60)

        env = np.exp(-t * 30)
        wave *= env

        sound = self._make_sound(wave)
        sound.set_volume(0.25)
        return sound

    # ─── Disparo ─────────────────────────────────────────
    def _generate_shoot(self):
        """Sonido de disparo (whoosh suave)."""
        sr = self.sample_rate
        dur = 0.18
        n = int(sr * dur)
        t = np.linspace(0, dur, n, endpoint=False)

        # Sweep ascendente
        freq = 200 + 400 * t / dur
        phase = np.cumsum(freq) / sr
        wave = np.sin(2 * np.pi * phase) * 0.3

        # Ruido de whoosh
        noise = np.random.randn(n) * 0.2
        noise *= np.sin(np.pi * t / dur)  # envolvente parabólica

        wave += noise
        env = np.sin(np.pi * t / dur) ** 0.5
        wave *= env

        sound = self._make_sound(wave)
        sound.set_volume(0.2)
        return sound

    # ─── Combo ───────────────────────────────────────────
    def _generate_combo(self, level=0):
        """Sonido de combo (arpegio ascendente)."""
        sr = self.sample_rate
        dur = 0.4
        n = int(sr * dur)
        t = np.linspace(0, dur, n, endpoint=False)

        # Notas del arpegio
        base = [523, 659, 784][min(level, 2)]  # C5, E5, G5
        wave = np.zeros(n)

        for i, mult in enumerate([1.0, 1.25, 1.5]):
            freq = base * mult
            start = int(i * 0.08 * sr)
            end = min(start + int(0.25 * sr), n)
            seg_t = np.linspace(0, (end - start) / sr, end - start, endpoint=False)
            note = np.sin(2 * np.pi * freq * seg_t) * 0.4
            note *= np.exp(-seg_t * 8)
            wave[start:end] += note

        sound = self._make_sound(wave)
        sound.set_volume(0.3)
        return sound

    # ─── Victoria ────────────────────────────────────────
    def _generate_win_fanfare(self):
        """Fanfarria de victoria — arpegio mayor ascendente con brillo."""
        sr = self.sample_rate
        dur = 2.5
        n = int(sr * dur)
        wave = np.zeros(n)

        # Secuencia de notas: C4, E4, G4, C5, E5, G5, C6
        notes = [262, 330, 392, 523, 659, 784, 1047]
        note_dur = 0.3
        gap = 0.05

        for i, freq in enumerate(notes):
            start = int(i * (note_dur - 0.1) * sr)
            end = min(start + int(note_dur * sr), n)
            seg_len = end - start
            seg_t = np.linspace(0, seg_len / sr, seg_len, endpoint=False)

            # Nota con armónicos
            note = np.sin(2 * np.pi * freq * seg_t) * 0.5
            note += np.sin(2 * np.pi * freq * 2 * seg_t) * 0.15
            note += np.sin(2 * np.pi * freq * 3 * seg_t) * 0.05

            # Envolvente
            env = np.exp(-seg_t * 4)
            env[:min(int(0.01 * sr), seg_len)] *= np.linspace(
                0, 1, min(int(0.01 * sr), seg_len))
            note *= env

            wave[start:end] += note

        # Acorde final sostenido
        chord_start = int(len(notes) * (note_dur - 0.1) * sr)
        chord_len = n - chord_start
        if chord_len > 0:
            seg_t = np.linspace(0, chord_len / sr, chord_len, endpoint=False)
            for freq in [523, 659, 784]:
                chord = np.sin(2 * np.pi * freq * seg_t) * 0.25
                chord += np.sin(2 * np.pi * freq * 2 * seg_t) * 0.08
                chord *= np.exp(-seg_t * 1.5)
                wave[chord_start:chord_start + chord_len] += chord

        sound = self._make_sound(wave)
        sound.set_volume(0.45)
        return sound

    # ─── Derrota ─────────────────────────────────────────
    def _generate_lose(self):
        """Sonido de derrota — tono descendente triste."""
        sr = self.sample_rate
        dur = 1.5
        n = int(sr * dur)
        t = np.linspace(0, dur, n, endpoint=False)

        # Glissando descendente
        freq = 400 * np.exp(-t * 1.2)
        phase = np.cumsum(freq) / sr
        wave = np.sin(2 * np.pi * phase) * 0.4

        # Segundo tono menor
        freq2 = 320 * np.exp(-t * 1.0)
        phase2 = np.cumsum(freq2) / sr
        wave += np.sin(2 * np.pi * phase2) * 0.2

        env = np.exp(-t * 1.5)
        wave *= env

        sound = self._make_sound(wave)
        sound.set_volume(0.35)
        return sound

    # ─── Botón hover ─────────────────────────────────────
    def _generate_button_hover(self):
        sr = self.sample_rate
        dur = 0.06
        n = int(sr * dur)
        t = np.linspace(0, dur, n, endpoint=False)
        wave = np.sin(2 * np.pi * 800 * t) * 0.2
        wave *= np.exp(-t * 30)
        sound = self._make_sound(wave)
        sound.set_volume(0.1)
        return sound

    # ─── Botón click ─────────────────────────────────────
    def _generate_button_click(self):
        sr = self.sample_rate
        dur = 0.1
        n = int(sr * dur)
        t = np.linspace(0, dur, n, endpoint=False)
        wave = np.sin(2 * np.pi * 600 * t) * 0.3
        wave += np.sin(2 * np.pi * 900 * t) * 0.15
        wave *= np.exp(-t * 30)
        sound = self._make_sound(wave)
        sound.set_volume(0.2)
        return sound

    # ═══════════════════════════════════════════════════════
    #  MÚSICA DE FONDO
    # ═══════════════════════════════════════════════════════

    def _steel_drum_note(self, freq, duration, vol=0.06):
        """Genera un tono tipo steel drum / marimba tropical."""
        sr = self.sample_rate
        n = int(sr * duration)
        t = np.linspace(0, duration, n, endpoint=False)

        # Armónicos típicos de steel drum (fundamental + 3ra + 5ta parcial)
        wave = np.sin(2 * np.pi * freq * t) * 1.0
        wave += np.sin(2 * np.pi * freq * 2.0 * t) * 0.5
        wave += np.sin(2 * np.pi * freq * 3.0 * t) * 0.25
        wave += np.sin(2 * np.pi * freq * 4.76 * t) * 0.12

        # Envolvente percusiva (ataque rápido, decay medio)
        env = np.exp(-t * 5.0)
        # Ataque suave
        attack = min(int(0.008 * sr), n)
        env[:attack] *= np.linspace(0, 1, attack)
        wave *= env * vol

        return wave

    def _build_background_music(self):
        """
        Genera música tropical alegre estilo Caribbean/Island.
        Usa steel drums, ritmo sincopado, bajo bouncy y progresión mayor.
        Fragmento de ~28 segundos con crossfade para loop seamless.
        """
        sr = self.sample_rate
        bpm = 115
        beat = 60.0 / bpm
        # 16 compases de 4/4 = 64 beats
        total_beats = 64
        dur = beat * total_beats
        n = int(sr * dur)
        wave = np.zeros(n)

        # ═══ PROGRESIÓN DE ACORDES (Mayor, alegre) ═══
        # C - G - Am - F  (la más alegre y pop)
        # Repetida 4 veces (4 beats cada acorde = 1 compás)
        chord_prog = [
            # C mayor
            (523, 659, 784),
            # G mayor
            (392, 494, 587),
            # Am (relativo menor, da variedad sin ser triste)
            (440, 523, 659),
            # F mayor
            (349, 440, 523),
        ]

        # ═══ CAPA 1: PAD BRILLANTE DE ACORDES ═══
        for rep in range(4):  # 4 repeticiones = 16 compases
            for ci, chord_freqs in enumerate(chord_prog):
                beat_offset = rep * 16 + ci * 4
                c_start = int(beat_offset * beat * sr)
                c_end = int((beat_offset + 4) * beat * sr)
                c_end = min(c_end, n)
                c_len = c_end - c_start
                if c_len <= 0:
                    continue

                ct = np.linspace(0, c_len / sr, c_len, endpoint=False)

                for freq in chord_freqs:
                    # Tono suave tipo ukulele/pad tropical
                    note = np.sin(2 * np.pi * freq * ct) * 0.03
                    note += np.sin(2 * np.pi * freq * 2 * ct) * 0.01

                    # Envolvente suave
                    fade = min(int(0.3 * sr), c_len // 3)
                    env = np.ones(c_len)
                    env[:fade] = np.linspace(0, 1, fade)
                    env[-fade:] = np.linspace(1, 0, fade)
                    note *= env

                    wave[c_start:c_end] += note

        # ═══ CAPA 2: MELODÍA STEEL DRUM ═══
        # Escala mayor pentatónica de C: C, D, E, G, A (alegre y tropical)
        mel_notes = [523, 587, 659, 784, 880, 1047, 1175, 1319]
        rng = np.random.RandomState(77)

        # Patrones rítmicos tropicales (en subdivisiones de beat)
        # 1 = nota, 0 = silencio, en semicorcheas
        tropical_patterns = [
            [1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0],
            [0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0],
            [1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1],
            [0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1],
        ]

        sub_beat = beat / 4  # semicorchea

        for rep in range(4):
            pattern = tropical_patterns[rep % len(tropical_patterns)]
            for ci, chord_freqs in enumerate(chord_prog):
                # Notas disponibles para este acorde (cercanas a las notas del acorde)
                chord_base = chord_freqs[0]
                available = [f for f in mel_notes
                             if abs(f - chord_base) < 500 or f in chord_freqs]
                if not available:
                    available = mel_notes

                for si, hit in enumerate(pattern):
                    if not hit:
                        continue

                    beat_pos = rep * 16 + ci * 4 + si * 0.25
                    start = int(beat_pos * beat * sr)
                    if start >= n:
                        continue

                    freq = available[rng.randint(0, len(available))]
                    note_dur = sub_beat * rng.choice([1.0, 1.5, 2.0])
                    note_samples = self._steel_drum_note(freq, note_dur, vol=0.055)

                    end = min(start + len(note_samples), n)
                    actual_len = end - start
                    wave[start:end] += note_samples[:actual_len]

        # ═══ CAPA 3: BAJO TROPICAL BOUNCY ═══
        # Notas de bajo siguiendo la progresión
        bass_freqs = [131, 98, 110, 87]  # C3, G2, A2, F2

        # Patrón de bajo sincopado (caribeño)
        bass_pattern = [
            (0.0, 0.4),  # beat 1
            (0.75, 0.2),  # antes del 2 (sincopado!)
            (1.5, 0.3),  # mitad del 2
            (2.0, 0.4),  # beat 3
            (2.75, 0.2),  # antes del 4
            (3.5, 0.25),  # mitad del 4
        ]

        for rep in range(4):
            for ci, bass_freq in enumerate(bass_freqs):
                for bp_offset, bp_dur in bass_pattern:
                    beat_pos = rep * 16 + ci * 4 + bp_offset
                    start = int(beat_pos * beat * sr)
                    seg_len = int(bp_dur * beat * sr)
                    end = min(start + seg_len, n)
                    actual_len = end - start
                    if actual_len <= 0:
                        continue

                    seg_t = np.linspace(0, actual_len / sr, actual_len,
                                        endpoint=False)

                    # Bajo con un poco de armónico (más calidez)
                    bass = np.sin(2 * np.pi * bass_freq * seg_t) * 0.09
                    bass += np.sin(2 * np.pi * bass_freq * 2 * seg_t) * 0.03

                    # Envolvente percusiva
                    env = np.exp(-seg_t * 6.0)
                    attack_s = min(int(0.01 * sr), actual_len)
                    env[:attack_s] *= np.linspace(0, 1, attack_s)
                    bass *= env

                    # Octava alta ocasional (bounce!)
                    if bp_offset in (0.75, 2.75):
                        hi = np.sin(2 * np.pi * bass_freq * 2 * seg_t) * 0.04
                        hi *= np.exp(-seg_t * 10)
                        bass += hi

                    wave[start:end] += bass

        # ═══ CAPA 4: RITMO PERCUSIVO SUAVE ═══
        # Shaker / hi-hat ligero para dar groove
        for beat_idx in range(total_beats):
            for sub in [0, 0.5]:  # en cada corchea
                pos = (beat_idx + sub) * beat
                start = int(pos * sr)
                dur_perc = 0.04
                p_len = min(int(dur_perc * sr), n - start)
                if p_len <= 0:
                    continue

                pt = np.linspace(0, p_len / sr, p_len, endpoint=False)

                # Ruido filtrado tipo shaker
                noise = np.random.randn(p_len) * 0.025
                noise *= np.exp(-pt * 50)

                # Acentuar beats fuertes (1 y 3)
                accent = 1.3 if (beat_idx % 4 in (0, 2) and sub == 0) else 0.7
                noise *= accent

                wave[start:start + p_len] += noise

        # ═══ CAPA 5: STRUM tipo ukulele/guitarra (offbeat) ═══
        for rep in range(4):
            for ci, chord_freqs in enumerate(chord_prog):
                # Offbeat strums (en el "y" de cada beat) — estilo reggae/ska
                for beat_off in [0.5, 1.5, 2.5, 3.5]:
                    beat_pos = rep * 16 + ci * 4 + beat_off
                    start = int(beat_pos * beat * sr)
                    strum_dur = 0.12
                    s_len = min(int(strum_dur * sr), n - start)
                    if s_len <= 0:
                        continue

                    st = np.linspace(0, s_len / sr, s_len, endpoint=False)
                    strum = np.zeros(s_len)

                    for fi, freq in enumerate(chord_freqs):
                        # Cada cuerda empieza ligeramente después (simula rasgueo)
                        delay = int(fi * 0.005 * sr)
                        if delay >= s_len:
                            continue
                        s_seg = st[delay:]
                        note = np.sin(2 * np.pi * freq * s_seg) * 0.025
                        note += np.sin(2 * np.pi * freq * 2 * s_seg) * 0.008
                        note *= np.exp(-s_seg * 15)
                        strum[delay:delay + len(note)] += note

                    wave[start:start + s_len] += strum

        # ═══ CROSSFADE PARA LOOP SEAMLESS ═══
        crossfade = int(1.5 * sr)
        if n > crossfade * 2:
            fade_out = np.linspace(1, 0, crossfade)
            fade_in = np.linspace(0, 1, crossfade)
            wave[-crossfade:] = (wave[-crossfade:] * fade_out +
                                 wave[:crossfade] * fade_in)

        self._music_sound = self._make_sound(wave)
        self._music_sound.set_volume(self._music_volume)

    # ═══════════════════════════════════════════════════════
    #  API PÚBLICA
    # ═══════════════════════════════════════════════════════

    def play_pop(self, variant=0):
        """Reproducir sonido de pop."""
        idx = variant % len(self._pop_sounds)
        self._pop_sounds[idx].play()

    def play_collision(self):
        """Sonido de burbuja adhiriéndose a la grilla."""
        self._collision_sound.play()

    def play_shoot(self):
        """Sonido de disparo."""
        self._shoot_sound.play()

    def play_combo(self, level=0):
        """Sonido de combo."""
        idx = min(level, len(self._combo_sounds) - 1)
        self._combo_sounds[idx].play()

    def play_win(self):
        """Fanfarria de victoria."""
        self._win_sound.play()

    def play_lose(self):
        """Sonido de derrota."""
        self._lose_sound.play()

    def play_button_hover(self):
        """Sonido al pasar sobre un botón."""
        self._button_hover.play()

    def play_button_click(self):
        """Sonido al hacer click en un botón."""
        self._button_click.play()

    # ─── Música ──────────────────────────────────────────

    def start_music(self):
        """Iniciar música de fondo en loop."""
        if self._music_sound and not self._music_playing:
            self._music_channel.play(self._music_sound, loops=-1)
            self._music_playing = True

    def stop_music(self):
        """Detener música de fondo."""
        self._music_channel.fadeout(1000)
        self._music_playing = False

    def set_music_volume(self, vol):
        """Ajustar volumen de la música (0.0 a 1.0)."""
        self._music_volume = max(0.0, min(1.0, vol))
        if self._music_sound:
            self._music_sound.set_volume(self._music_volume)

    def is_music_playing(self):
        return self._music_playing

    # ─── Limpieza ────────────────────────────────────────

    def cleanup(self):
        """Liberar recursos de audio."""
        self.stop_music()
        pygame.mixer.quit()
