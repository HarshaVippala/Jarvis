# Jarvis Desktop UI Mockups

## Floating Orb States

### Idle State
```
    ┌───┐
    │ J │
    └───┘
```

### Active/Pulsing State
```
   ╭─────╮
   │  J  │
   ╰─────╯
```

### Listening State
```
  ╭───────╮
  │ ▮▮▮▯▯▯ │
  ╰───────╯
```

### Processing State
```
  ╭───────╮
  │   ⟳   │
  ╰───────╯
```

## Response UI States

### Confirmation (Brief)
```
  ╭──────────────────────╮
  │                      │
  │  Command executed!   │
  │                      │
  ╰──────────────────────╯
```

### Information Display
```
  ╭──────────────────────────────────────╮
  │ Current Weather                      │
  │ ──────────────────                   │
  │ 72°F and sunny in San Francisco      │
  │ Humidity: 54%  Wind: 8mph NW         │
  │                                      │
  │                          [✕] [📌]    │
  ╰──────────────────────────────────────╯
```

### Code/Technical Content
```
  ╭──────────────────────────────────────────────╮
  │ Python Function                              │
  │ ──────────────────                           │
  │ def calculate_area(radius):                  │
  │     """Calculate the area of a circle."""    │
  │     return 3.14159 * radius * radius         │
  │                                              │
  │ [Copy] [Open in Editor] [Save As] [✕] [📌]   │
  ╰──────────────────────────────────────────────╯
```

### List Content
```
  ╭──────────────────────────────────────╮
  │ Shopping List                        │
  │ ──────────────────                   │
  │ • Milk                               │
  │ • Eggs                               │
  │ • Bread                              │
  │ • Apples                             │
  │                                      │
  │ [Copy] [Send to Phone] [✕] [📌]      │
  ╰──────────────────────────────────────╯
```

## Activity Log Panel

```
  ╭──────────────────────────────────────────────────────────────────╮
  │ Activity Log                                            [✕]      │
  │ ──────────────────                                               │
  │                                                                  │
  │  Today, 8:15 AM                                                  │
  │  ▶ You: "What's the weather today?"                              │
  │  ▶ Action: Searched web for "current weather"                    │
  │                                                                  │
  │  Today, 8:12 AM                                                  │
  │  ▶ You: "Open VS Code"                                           │
  │  ▶ Action: Launched application "Visual Studio Code"             │
  │                                                                  │
  │  Yesterday, 4:30 PM                                              │
  │  ▶ You: "Create a new folder called Projects"                    │
  │  ▶ Action: Created directory ~/Projects                          │
  │                                                                  │
  │                                                                  │
  │  [Clear History] [Export Log]                  [Show Details ▼]  │
  ╰──────────────────────────────────────────────────────────────────╯
```

## Settings Panel

```
  ╭──────────────────────────────────────╮
  │ Settings                     [✕]     │
  │ ──────────────────                   │
  │                                      │
  │ Voice Activation:  [ON]              │
  │ Wake Word:         "Jarvis"          │
  │ Voice:             [Male] [Female]   │
  │ Display Duration:  [ Auto ]          │
  │                                      │
  │ Cost Tracking:     [ON]              │
  │ API Keys:          [Configure...]    │
  │                                      │
  │ [Reset] [Save] [Cancel]              │
  ╰──────────────────────────────────────╯
```

## Cost Dashboard

```
  ╭──────────────────────────────────────────────╮
  │ API Usage                            [✕]     │
  │ ──────────────────                           │
  │                                              │
  │ Current Session:   $0.12                     │
  │ This Month:        $3.47                     │
  │ Last Month:        $5.23                     │
  │                                              │
  │ ┌───────────────────────────────────┐        │
  │ │                                   │        │
  │ │       [Usage Graph Here]          │        │
  │ │                                   │        │
  │ └───────────────────────────────────┘        │
  │                                              │
  │ Model Used:        GPT-4                     │
  │ Tokens Used:       12,432                    │
  │                                              │
  │ [Detailed Report] [Reset Counter]            │
  ╰──────────────────────────────────────────────╯
```

## Multi-Monitor Support

```
┌─────────────────────┐      ┌─────────────────────┐
│                     │      │                     │
│      Monitor 1      │      │      Monitor 2      │
│                     │      │                     │
│                     │      │                     │
│                     │      │     ╭───────╮      │
│                     │      │     │   J   │      │
│                     │      │     ╰───────╯      │
│                     │      │                     │
└─────────────────────┘      └─────────────────────┘
          Orb follows active monitor
```

## System Tray Menu

```
┌─────────────────────────┐
│ ✓ Enable Jarvis         │
│ ✓ Start at Login        │
│ ─────────────────────── │
│   Voice Settings        │
│   Display Settings      │
│   Activity Log          │
│   Cost Dashboard        │
│ ─────────────────────── │
│   About Jarvis          │
│   Quit                  │
└─────────────────────────┘