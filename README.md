# chat-bridgee

開發想法來自 [`TISUnion/ChatBridge`](https://github.com/TISUnion/ChatBridge) minecraft mcdr chat bridge 實現

```mermaid
flowchart LR
  subgraph Minecraft Host
    Survival[Minecraft Survival Server]
    Create[Minecraft Create Server]
    Mirror[Minecraft Mirror Server]
    server_else(...)
  end
  MCDR("mcdr-ChatBridgeE-plugin") <--> Survival & Create & Mirror & server_else

  subgraph server plugins
    plugin_discord(discord)
    else_plugin(...)
  end
  plugins <--> plugin_discord & else_plugin

  subgraph cli commands
    cli_reload(plugin reload)
    cli_add(plugin add)
    cli_remove(plugin remove)
    cli_list(plugin list) 
    cli_else(...)
  end
  cli --> cli_reload & cli_add & cli_remove & cli_list & cli_else

  server(ChatBridgeE Server)
  client <--> MCDR
  server <--> client & plugins & cli
```

## 參考

1. [`discord.py cog load method`](https://github.com/Rapptz/discord.py)
2. [`carpet-scripts:format function`](https://github.com/gnembon/fabric-carpet/blob/master/docs/scarpet/Full.md#formatcomponents--formatcomponents-)
