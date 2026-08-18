'use strict';

const assert=require('assert');
const Model=require('../fabric-inspection/quality-model.js');

const state=Model.normalizeState({
  records:[
    {inspection_id:'FI-1',inspection_scope:'FABRIC_TEST',inspection_result:'PASS',photo_capture_id:'PC-1',photo_refs:[],created_at:'2026-08-18T00:00:00Z'},
    {inspection_id:'FI-2',inspection_scope:'APPEARANCE',inspection_result:'NEEDS_REVIEW',defect_category:'COLOR_VARIATION',photo_refs:['drive://photo'],created_at:'2026-08-18T01:00:00Z'},
    {inspection_id:'FI-3',inspection_scope:'FABRIC_TEST',inspection_result:'FAIL',created_at:'2026-08-18T02:00:00Z'}
  ],
  review_events:[
    {review_id:'FR-1',inspection_id:'FI-1',decision:'APPROVED',created_at:'2026-08-18T03:00:00Z'},
    {review_id:'FR-2',inspection_id:'FI-2',decision:'RETURNED',created_at:'2026-08-18T04:00:00Z'}
  ],
  improvement_events:[
    {improvement_id:'FC-1',inspection_id:'FI-3',status:'OPEN',created_at:'2026-08-18T05:00:00Z'},
    {improvement_id:'FC-2',inspection_id:'FI-3',status:'VERIFIED',created_at:'2026-08-18T06:00:00Z'}
  ]
});

const summary=Model.computeSummary(state);
assert.strictEqual(summary.total,3);
assert.strictEqual(summary.pass,1);
assert.strictEqual(summary.fail,1);
assert.strictEqual(summary.needsReview,1);
assert.strictEqual(summary.appearance,1);
assert.strictEqual(summary.pending,2);
assert.strictEqual(summary.approved,1);
assert.strictEqual(summary.photoEvidence,2);
assert.strictEqual(summary.improvementCases,1);
assert.strictEqual(summary.openImprovements,0);
assert.strictEqual(summary.closedImprovements,1);
assert.strictEqual(summary.failRate,33);

assert.strictEqual(Model.matchesFilter(state.records[1],'pending',state),true);
assert.strictEqual(Model.matchesFilter(state.records[0],'pending',state),false);
assert.strictEqual(Model.matchesFilter(state.records[2],'fail',state),true);
assert.strictEqual(Model.matchesFilter(state.records[1],'appearance',state),true);
assert.strictEqual(Model.matchesFilter(state.records[2],'improvement',state),true);
assert.strictEqual(Model.matchesFilter(state.records[0],'photo',state),true);

console.log('PASS: quality-model summary and filters behave as expected');
