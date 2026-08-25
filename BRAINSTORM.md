**Motivation**: The Louvre break in
Museum / archive / cultural heritage storage

* Tilt sensor on display cases — real museums do use case-tamper sensors; this is a legitimate, not-stretched use of exactly the sensor you have.
* DHT11 climate monitoring — archives and museums are extremely strict about temperature/humidity for preservation (paper, textiles, paintings degrade outside narrow bands)
* Fire detection with false-positive suppression matters enormously here — unlike most buildings, you generally can't use water-based suppression near artifacts, so early, reliable, low-false-positive detection is disproportionately valuable — a good talking point for why your corroboration logic matters.
* Keypad access control for restricted collections/archive rooms.
  * 3 fails: send notif to security + 30s lock / need security overwrite
  * 5 fails: buzzer (need to make sure it not going forever) +flashing light on + call police
* Water leak/flooding for underground archives
* Breakin:
  * Sound sensor + vibration
  * Motion sensor for the display case from inside. It has low detection range, could has false detection
