# StudioNet proofs

[StudioNet deployment](https://explorer-studio.genlayer.com/address/0x9F55d7560F13811E1b7d4807027517faEfA3bb33) · [Deployed source](https://github.com/Al1ranger/register-trace-witness/blob/12d6ae88200d12daa6bc5f52ef53b5ea24b743b4/contracts/RegisterTraceWitness.py) · [Synthetic fixtures](https://github.com/Al1ranger/register-trace-witness/tree/12d6ae88200d12daa6bc5f52ef53b5ea24b743b4/fixtures) · [Receipt and readback data](PROOFS.json)

Deployed source matched the pinned commit. Normalized source SHA-256 is `34ab8263fa44181baa87bd3008c6de267318cff397e791a0d9b3aac53d0ebb8f`.
Each receipt finalized with successful execution and majority agreement.

A [hosted verification run](https://github.com/Al1ranger/register-trace-witness/actions/runs/44281884416) resumed the recorded deployment and signed the fixture calls with a temporary StudioNet account.

| Transaction | Outcome | Independently verified readback |
| --- | --- | --- |
| [deploy](https://explorer-studio.genlayer.com/tx/0xe67a0b7cf106b40b8c8f9172cda09861ca1aed7164c6614631d8e6899b402cb7) | Deployed | Source match |
| [overlap](https://explorer-studio.genlayer.com/tx/0x3c5a5bc14d9a71560bf0a56cdb0e06f5b8cce95d99ee1c650b0ecf65c98b66d9) | DETERMINATE | Overlapping writes allow order B, A, C, D, E, F. Continuation returns 3. |
| [stale-read](https://explorer-studio.genlayer.com/tx/0x4daa707f96a3f782624d50d87e4ca5d95e89d5de6b6d52898a56f049d158fb01) | INCONSISTENT | Serial writes make the same read impossible. Continuation reverts. |
| [two-terminals](https://explorer-studio.genlayer.com/tx/0x81e19702ff57cdf3a773f3db0d00d0a003cf9f5b41f2a9c2f4de892e8f64a8c3) | AMBIGUOUS | Both final values 1 and 2 have a witness. Continuation reverts. |

The first two fixtures have identical method arguments and responses. Changing the event order alone changes whether a valid sequential execution exists. All three fixtures are synthetic.
