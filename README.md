# Tecom Discovery for Home Assistant

Local Home Assistant integration for an Aritech/Tecom Discovery panel using
the panel's onboard HTTPS API.

## Current status

This first release supports:

- Discovery email/password authentication and bearer-token renewal
- panel firmware/API information
- PIR/motion inputs as movement binary sensors using `Detected`/`Clear`
- other input states as sensors using the panel's `Sealed`/`Unsealed`
  terminology
- relay states as read-only binary sensors
- area states as alarm control panels with optional keypad-protected control
- local polling every 10 seconds

Area arm/disarm commands require a Home Assistant keypad code configured in
the integration options. The Discovery panel authorizes the underlying command
through the dedicated service account and its assigned alarm group.

## Releases

- **Beta 06 / 0.1.5:** Add keypad-protected full-arm, stay-arm, and disarm
  controls using the Discovery panel's native area action API.
- **Beta 05 / 0.1.4:** Add an input configuration wizard for selecting each
  detected input's Home Assistant area and sensor type.
- **Beta 04 / 0.1.3:** Automatically expose inputs named PIR, motion, or
  movement as Home Assistant movement sensors.
- **Beta 03 / 0.1.2:** Show input states as `Sealed`/`Unsealed` and remove the
  superseded Safe/Unsafe binary-sensor entities.
- **Beta 02 / 0.1.1:** Correctly map `disarmed` areas before checking armed
  state names.
- **Beta 01 / 0.1.0:** Initial read-only release.

## Installation

### HACS

1. Open HACS and select **Integrations**.
2. Open the menu and choose **Custom repositories**.
3. Add `https://github.com/rodgrech/tecom-discovery-home-assistant` as an
   **Integration** repository.
4. Install **Tecom Discovery**, restart Home Assistant, and add the integration
   from **Settings → Devices & services**.

### Manual

Copy `custom_components/tecom_discovery` into the Home Assistant configuration
directory:

```text
config/
└── custom_components/
    └── tecom_discovery/
```

Restart Home Assistant. Go to **Settings → Devices & services → Add
integration**, search for **Tecom Discovery**, and enter:

- panel address, for example `192.168.1.99`
- the dedicated panel user's email and password
- the highest configured input, area and relay numbers

Discovery commonly uses a self-signed certificate, so leave certificate
verification disabled unless a trusted certificate has been installed.

## Security

Create a dedicated panel user with only the permissions needed to view status.
Do not expose the panel web interface to the internet. Home Assistant and the
panel should communicate across a trusted local network or restricted VLAN.

Credentials are stored in Home Assistant's config-entry storage in the same
way as other integrations.

## Diagnostics and development

The integration calls these observed local API endpoints:

- `auth/sign-in`
- `panel/getinfo`
- `recallInputStatus`
- `recallAreaStatus`
- `recallRelayStatus`

Discovery firmware versions may vary in their response envelope and field
names. The client normalizes common variants and retains the original response
fields as entity attributes. If an entity remains unavailable, enable debug
logging and provide a redacted response:

```yaml
logger:
  logs:
    custom_components.tecom_discovery: debug
```

Never include passwords, bearer tokens, user records, card data, or PINs in a
bug report.
