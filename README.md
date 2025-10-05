NOTE: this is individual maintenance of GUI Sir Squirrel Assistant which previously maitained by [Kryxzort](https://github.com/Kryxzort) (kudo to him!). I want to fork this and provide my own version because their is a lot of spaghetti code inside this repo, which give a cooperate nerd like me a goosebumps. If everyone support, I'm happy to contribute back to the original repo (though, only in this year 2025 as I planed to drop this game afterward due to life).
Here is Kryxzort' discord link: [Join my Discord fr](https://discord.gg/vccsv4Q4ta)

Any issue with this specific fork, please open issue 

# Sir Squirrel Assistant

Sir Squirrel Assistant is a helpful tool for the game Limbus Company by Project Moon. No longer will you need to hit the mines as Sir Squirrel will do it for you.

# Features

There are already other auto mirror dungeon tools out there so why should you use Sir Squirrel instead. Well here's why

- im always improving and optimizing stuff, adding suggestions and features
- its really really fast, faster than any other macro on the market according to my knowledge
- has great QOL features like chain automations like 3 threads then 2 exp then 20 mirror dungeon
- supports multi monitor and any resolution(even weird ones supported if you tinker with offsets using simple gui) man cmon you aint finding this nowhere else!!!!
- auto reconnect
  - auto reconnect when internet reachable(so peak)
- very customizable
- E.G.O Gift Choice
  - The ability to choose which status you want to use throughout the run
- Auto Squad Rotation
  - In conjuction with the E.G.O Gift Choice you can also choose multiple statuses and Sir Squirrel will cycle through them every one and follow the gifts accordingly
  - Choose the squad order for each team and Sir Squirrel will follow it
- Pack Selection
  - Automatically choose packs based off your E.G.O Gift as well as using a priority list for packs for each floor
  - Filters for duplicate gifts automatically
- E.G.O Gift Enhancement
  - Sir Squirrel upgrades E.G.O Gifts of the status you chose along with keywordless gifts at rest stops
- E.G.O Gift Purchase
  - Sir Squirrel purchases E.G.O Gifts according to the status you chose as well as keywordless gifts
- E.G.O Usage
  - Sir Squirrel now uses E.G.O in battle for unfavorable clashes
- E.G.O Gift Fusion
  - Sir Squirrel will fuse other E.G.O types to get better gifts.

# Planned Features

Top priority
- [ ] Add support for MDH
- [x] Add support for multiple different screen resolution
- [ ] Add more stop break to allow breaking out of macro loop when something go wrong
- [ ] Improve customizability
  - [ ] Add toggle for each step in each workflow (e.g. toggle off enkhapalin conversion)
  - [ ] Move all configurable from code to the file and allow customize via CLI/GUI for common things in future update (e.g. add support for new MD package)
- [ ] Add support for both GUI and CLI version
- [ ] Reduce code smell (I will do this will time to time)
  - [ ] Remove redundant functions with no usage
  - [ ] Add type hint and formatting
  - [ ] Improve log redability

Low priority (these are things I want, but on a whim and I don't know how to do and how long woulod it take, so it go there)
- [ ] Improve performance/Reduce resource consumption
- [ ] Improve documentation
- [ ] Improve debug feature
- [ ] Move to PyQT or PySide (official QT binding by QT themself)
- [ ] Game played by chatGPT (hehe, just me being dillusioned)

# Known Issues

- E.G.O Usage might not work on very low resolutions (1280x720)

# Troubleshooting

[in the discord again ofc!!!! (in reality i just want members i can flex)](https://discord.gg/xvGwFMsYfM)

# Bug Reporting

Please let me know about any issues you face with Sir Squirrel and I will do my best to look into it.

[bug report here please](https://discord.gg/JY4v3t9cRa)

make sure that bug is not already reported, if it has then type Bump on that post and provide relevant information

please follow the format in the pinned post

# Instructions

1. Download and install `uv` (follow [this instruction](https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_2)). `uv` is a new and very popular Python package manager, which will handle version control, ensure you can run script without issue.
2. Open Terminal (`cmd` or `Powershell`) and run `uv install` if this is the first time you clone this repo. Make sure your current directory is in `GuiSirSquirrelAssistant`, not `all data`.
3. Run these scripts to start the GUI:
```Powershell
cd "all data"
uv run gui_launcher.py
```
Note: why I remove all `.bat` script and `.vbs`? Well, running script without checking it yourself is a fucking bad practice from security POV and can get blocked by Windows Defense. So I want this instruction to be as transparent as possible. Please bear with it and get your hand dirty by start touching terminal. 

From there everything is intuitive though i do have explainations in the "Help" section

Enjoy and give me a star if you liked >:) keeps me motivated to see 100 stars on my repo (i have 12😭)

