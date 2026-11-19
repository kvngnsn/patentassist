# Specification

## TITLE

Helmet Turn-Signal System With Wireless Handlebar Remote

## CROSS-REFERENCE TO RELATED APPLICATIONS

This application claims the benefit of U.S. Provisional Application No. 63/123,456, filed March 3, 2026, which is incorporated herein by reference in its entirety.

## BACKGROUND

Cyclists signal turns by hand, which takes a hand off the handlebar. Some helmets carry lights, but the lights are not controlled from the handlebar.

## SUMMARY

In some embodiments, a helmet includes a shell, a rear light array, and a controller that drives the rear light array in response to a wireless signal from a handlebar remote.

## BRIEF DESCRIPTION OF THE DRAWINGS

FIG. 1 is a block diagram of a helmet signal system according to some embodiments.

FIG. 2 is a flowchart of a method of signaling a turn.

FIG. 3 is a sequence diagram of messages exchanged during a turn signal.

FIGS. 4 and 5 show a configuration screen and a light-output graph, respectively.

## DETAILED DESCRIPTION

Referring to FIG. 1, a helmet 100 includes a controller 110, a rear light array 120, a battery 130, and a wireless receiver 140. A handlebar remote 150 sends a signal over a **wireless link** to the wireless receiver 140. A mobile device 160 may also configure the controller 110 through the wireless receiver 140. The battery 130 supplies about 3.7 V to the controller 110.

FIG. 2 shows a method. At step 202, the controller 110 powers on. At step 204, the controller receives a signal from the handlebar remote 150. At decision 206, the controller determines whether the signal is a left or right signal. For a left signal, step 208 flashes a left segment of the rear light array 120; for a right signal, step 210 flashes a right segment. At decision 212, if a cancel signal is received, step 214 turns off the rear light array 120; otherwise the method returns to step 204.

As shown in FIG. 3, the handlebar remote 150 sends a turn request 302 to the wireless receiver 140, which forwards a decoded command 304 to the controller 110. The controller 110 starts a timer 306 and sends a flash pattern 308 to the rear light array 120, then sends an acknowledgment 310 back to the handlebar remote 150.

FIG. 4 shows the mobile device 160 displaying a settings header 402, a brightness control 404, a pattern list 406, a save button 408, and a battery icon 410. Each pattern in the pattern list 406 lasts 10 seconds or less.

FIG. 5 plots rear light output 502 against ambient light, along with a minimum output 504 of 30 %.

- In one embodiment, the rear light array 120 includes 12 LEDs.
- In another embodiment, the shell is polycarbonate.

## CLAIMS

See claims.md.

## ABSTRACT

A helmet includes a rear light array and a controller. A wireless receiver in the helmet receives turn signals from a handlebar remote, and the controller flashes the left or right segment of the rear light array in response. A mobile device can configure flash patterns and brightness, and the light output falls as ambient light rises.
