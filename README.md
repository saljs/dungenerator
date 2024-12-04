# Dungenerator

Dungenerator is a tool I made to help me make, edit, and display maps for an RPG
game that I am running involving a huge (dozens of levels, multiple square 
kilometers per level) mega-dungeon. To speed up the map-drawing process, I made
the `dungen` tool. It takes a YAML input that specifies the general layout of
the dungeon as well as different kinds of levels and how to draw them. It then
creates a "Dungen" savefile, as well as optionally saving the level SVG files.

DMScreen is a Flask web application that allows you to open, edit, and run
"Dungen" save files. I chose to do this portion as a web app for two reasons:
 * Browser rendering support for SVGs is superb; much better than any library I
could find that would render them locally.
 * I wanted to be able edit my dungeons from anywhere, across multiple devices
(just not mobile yet).
