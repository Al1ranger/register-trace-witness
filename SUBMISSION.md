**Contribution type** Builder → Intelligent Contracts

**Title** RegisterTraceWitness — Consensus-Checked Register Histories

**Notes / Description**

RegisterTraceWitness reconstructs possible final values from concurrent reads, writes and compare-and-swap operations. The leader and validators independently fetch a commit-pinned invocation/response trace, verify its SHA-256, and exhaustively recompute the sequential orders consistent with real time and returned values. Agreement covers the normalized operations and one witness order per final value. A consumer can retrieve a continuation value only when every valid order ends at that value.

StudioNet demonstrations used synthetic traces. Overlapping writes yielded a unique terminal value of 3. Serializing those writes made the same read impossible. Removing the later observations left both 1 and 2 possible. The contract supports one register and at most eight completed operations per trace.

**Evidence**

- [Repository](https://github.com/Al1ranger/register-trace-witness)
- [Deployed source](https://github.com/Al1ranger/register-trace-witness/blob/12d6ae88200d12daa6bc5f52ef53b5ea24b743b4/contracts/RegisterTraceWitness.py)
- [StudioNet deployment](https://explorer-studio.genlayer.com/address/0x9F55d7560F13811E1b7d4807027517faEfA3bb33)
- [Proof ledger](https://github.com/Al1ranger/register-trace-witness/blob/main/LIVE_PROOFS.md)
- [deploy](https://explorer-studio.genlayer.com/tx/0xe67a0b7cf106b40b8c8f9172cda09861ca1aed7164c6614631d8e6899b402cb7)
- [overlap](https://explorer-studio.genlayer.com/tx/0x3c5a5bc14d9a71560bf0a56cdb0e06f5b8cce95d99ee1c650b0ecf65c98b66d9)
- [stale-read](https://explorer-studio.genlayer.com/tx/0x4daa707f96a3f782624d50d87e4ca5d95e89d5de6b6d52898a56f049d158fb01)
- [two-terminals](https://explorer-studio.genlayer.com/tx/0x81e19702ff57cdf3a773f3db0d00d0a003cf9f5b41f2a9c2f4de892e8f64a8c3)
