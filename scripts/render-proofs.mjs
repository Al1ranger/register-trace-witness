import assert from 'node:assert/strict';
import fs from 'node:fs';

const repo = 'https://github.com/Al1ranger/register-trace-witness';
const explorer = 'https://explorer-studio.genlayer.com';
const proof = JSON.parse(fs.readFileSync('PROOFS.json', 'utf8'));
assert.equal(proof.verified, true);
assert.equal(proof.source.source_match, true);
assert.match(proof.source_commit, /^[a-f0-9]{40}$/);
assert.match(proof.address, /^0x[a-fA-F0-9]{40}$/);
assert.deepEqual(proof.transactions.map(tx => tx.step), ['deploy', 'overlap', 'stale-read', 'two-terminals']);
const links = proof.transactions.map(({step, hash, receipt}) => {
  assert.match(hash, /^0x[a-f0-9]{64}$/);
  assert.equal(receipt.status, 'FINALIZED');
  assert.equal(receipt.execution, 'SUCCESS');
  assert.equal(receipt.consensus, 'MAJORITY_AGREE');
  assert(receipt.committed && receipt.agree_votes >= 2 && receipt.leader_only === false);
  return `[${step}](${explorer}/tx/${hash})`;
});
const {overlap, 'stale-read': stale, 'two-terminals': ambiguous} = proof.examples;
assert.equal(overlap.record.outcome.status, 'DETERMINATE');
assert.deepEqual(overlap.checks, {continuation: 3});
assert.equal(stale.record.outcome.status, 'INCONSISTENT');
assert.equal(ambiguous.record.outcome.status, 'AMBIGUOUS');
assert(stale.checks.continuation_reverted && ambiguous.checks.continuation_reverted);
const contract = `[StudioNet deployment](${explorer}/address/${proof.address})`;
const source = `[Deployed source](${repo}/blob/${proof.source_commit}/contracts/RegisterTraceWitness.py)`;
const fixtures = `[Synthetic fixtures](${repo}/tree/${proof.source_commit}/fixtures)`;
const ledger = `[Proof ledger](${repo}/blob/main/LIVE_PROOFS.md)`;

fs.writeFileSync('LIVE_PROOFS.md', [
  '# StudioNet proofs', '',
  `${contract} · ${source} · ${fixtures} · [Receipt and readback data](PROOFS.json)`, '',
  `Deployed source matched the pinned commit. Normalized source SHA-256 is \`${proof.source.sha256}\`.`,
  'Each receipt finalized with successful execution and majority agreement.', '',
  `A [hosted verification run](${repo}/actions/runs/44281884416) resumed the recorded deployment and signed the fixture calls with a temporary StudioNet account.`, '',
  '| Transaction | Outcome | Independently verified readback |',
  '| --- | --- | --- |',
  `| ${links[0]} | Deployed | Source match |`,
  `| ${links[1]} | DETERMINATE | Overlapping writes allow order B, A, C, D, E, F. Continuation returns 3. |`,
  `| ${links[2]} | INCONSISTENT | Serial writes make the same read impossible. Continuation reverts. |`,
  `| ${links[3]} | AMBIGUOUS | Both final values 1 and 2 have a witness. Continuation reverts. |`, '',
  'The first two fixtures have identical method arguments and responses. Changing the event order alone changes whether a valid sequential execution exists. All three fixtures are synthetic.', '',
].join('\n'));

fs.writeFileSync('SUBMISSION.md', [
  '**Contribution type** Builder → Intelligent Contracts', '',
  '**Title** RegisterTraceWitness — Consensus-Checked Register Histories', '',
  '**Notes / Description**', '',
  'RegisterTraceWitness reconstructs possible final values from concurrent reads, writes and compare-and-swap operations. The leader and validators independently fetch a commit-pinned invocation/response trace, verify its SHA-256, and exhaustively recompute the sequential orders consistent with real time and returned values. Agreement covers the normalized operations and one witness order per final value. A consumer can retrieve a continuation value only when every valid order ends at that value.',
  '',
  'StudioNet demonstrations used synthetic traces. Overlapping writes yielded a unique terminal value of 3. Serializing those writes made the same read impossible. Removing the later observations left both 1 and 2 possible. The contract supports one register and at most eight completed operations per trace.',
  '',
  '**Evidence**', '',
  `- [Repository](${repo})`,
  `- ${source}`, `- ${contract}`, `- ${ledger}`,
  ...links.map(tx => `- ${tx}`), '',
].join('\n'));
