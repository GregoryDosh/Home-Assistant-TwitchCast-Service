# Home-Assistant-TwitchCast-Service

# Installation/Usage

## Git Clone
You can clone this repo into your `custom_components` folder in your Home Assistant config location with the name `twitchcast`.
```bash
git clone git@github.com:GregoryDosh/Home-Assistant-TwitchCast-Service.git twitchcast
```

## Git Submodule
You can also add it as a submodule which will allow you to pull updates in the future using `git submodule foreach git pull`.
```bash
git submodule add -b master git@github.com:GregoryDosh/Home-Assistant-TwitchCast-Service.git twitchcast
```


## Example Configuration
```yaml
twitchcast:
  chromecast_name: Living Room TV
  layout: right

```

## Services
### twitchcast.cast_stream
**channel**: Channel name
**layout** (optional): `left`, `right`, `top`, `bottom`

```json
{
    "channel": "monotonetim",
    "layout": "right"
}
```
