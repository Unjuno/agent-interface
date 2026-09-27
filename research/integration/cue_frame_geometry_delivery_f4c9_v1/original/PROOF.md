# Coordinate proof and limits

This is elementary translation algebra under an explicit coordinate contract, not
a novel localization algorithm. Cue meaning is "this surface-local region in this
referenced frame", not "whatever occupies this physical screen position now".

## Variables
|Symbol|意味（日本語）|SI単位|Definition|Domain/assumption|Type|
|---|---|---|---|---|---|
|s|参照画像上の画面ROI左上|1（pixel格子座標、mへの換算なし）|root-screen coordinate at cue reference|Z²|integer vector|
|o_f|参照画像取得時のウィンドウ原点|1（pixel）|window origin in that root screen|Z², same screen|integer vector|
|o_n|受信時のウィンドウ原点|1（pixel）|later window origin|Z², same incarnation|integer vector|
|q|意図したローカルROI左上|1（pixel）|s-o_f|inside retained window|integer vector|
|q_w|後の位置を誤用したローカルROI左上|1（pixel）|s-o_n|inside window for directed tests|integer vector|
|e|ローカル座標誤差|1（pixel）|q_w-q|Z²|integer vector|
|w,h|ROIの幅と高さ|1（pixel数）|both32 in this pilot|positive integers|integer scalars|
|B|2クロップのRGB本体byte数|1（octet数）|2·w·h·3|two images,RGB8|integer scalar|

## Assumptions
The window is borderless and is translated only. There is no scale, rotation,
scroll, reflow or object motion in the local coordinate system. The reference
image and its origin have the same trusted surface incarnation and a quiescent
capture interval. Required metadata and exact bytes exist. A move does not change
incarnation identity. A replacement is a different instance and is refused by this
active-generation API even when old images remain archived.

## Derivation
1. In a translated window the root-screen and local coordinates obey s=o_f+q.
   This is the definition of the root origin and the window-local origin.
2. Subtract o_f from both sides. The reference-bound local coordinate is q=s-o_f.
3. A current-geometry converter instead returns q_w=s-o_n.
4. Subtract q from q_w:
   e=q_w-q=(s-o_n)-(s-o_f)=o_f-o_n.
5. If o_n=o_f, e=(0,0). Otherwise at least one component of e is nonzero. Thus
   equal window ID alone does not imply equal mapping for an old screen coordinate.
6. Under the assumptions, substituting the referenced origin in step2 recovers
   q exactly; the two retained temporal window images can be cropped at q.
7. Different coordinates do not necessarily imply different pixels (a flat or
   repeated image can hide the error). Therefore the live fixture uses different
   non-flat neighboring panels and retains independent full-root screenshots.
   Its auditor checks pixel differences rather than inferring them from e alone.

## Numerical example and unit check
s=(144,80), o_f=(96,64) give q=(48,16). After moving right32pixels,
o_n=(128,64), so q_w=(16,16) and e=(-32,0). All operands are integer coordinates
in one pixel grid, so subtraction is dimensionally valid. Pixels are not metres;
no physical-length or DPI accuracy follows.
B=2·32·32·3=6144octets. This is RGB payload only, not Base64, JSON, history acquisition,
wire, token or cumulative budget. Every accepted policy uses the same payload cap.

## Refusal and authority boundary
If the reference cannot be uniquely identified, its hash/scope disagrees, or the
current incarnation differs, this contract does not have premises for step2's
active-context use. The implemented explicit HOLD/REJECT is part of the declared
policy; the algebra does not mandate this particular archival API design.

The adapter has no input/display API, and the exact inherited extractor returns
only images and false authority/input/lease/effect flags. No operation in these
functions emits task input. This structural argument assumes the trusted program
and standard dependencies; it is not a sandbox proof for arbitrary hostile code.
The separate live journals and before/after observations test composition under
this assumption. Crop correctness is not action permission or task success.

## ERROR CHECK
Different time coordinate frames are never subtracted as if identical. A later
capture is excluded from the inherited historical extraction by cue time. Motion
and incarnation change are separate. Algebra establishes coordinate equality,
not pixel distinctness, source authenticity, general GUI mapping or human benefit.
There is no statistical or timing-uncertainty inference from this finite matrix.
