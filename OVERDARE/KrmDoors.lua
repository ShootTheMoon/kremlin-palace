--!strict
-- Kremlin Palace — 문 개폐 (런타임)
-- FBX는 애니메이션을 안 싣는다. 대신 각 문을 힌지 원점 FBX로 뽑아 두었으므로
-- 엔진에서 힌지 CFrame에 Y축 회전만 곱하면 그대로 열린다.
--
-- 사전 준비
--   1. 04_DOORS\*.fbx 10개를 임포트한다.
--   2. MeshPart 하나씩 만들고 MeshId 에 **STATIC_MESH** 에셋 id 를 넣는다
--      (MODEL id 는 에디터에선 보이지만 플레이 중 안 보인다).
--   3. 각 MeshPart 의 Name 을 아래 DOORS 의 key 와 맞춘다.
--   4. Anchored = true, CanCollide = true.
--
-- 좌표: doors.json 의 hinge_X/Y/Z_cm 을 그대로 쓴다 (이미 OVERDARE cm Y-up).

local TweenService = game:GetService("TweenService")

-- doors.json 에서 생성. {이름 = {힌지위치, 기준yaw, 열림각, 지속시간}}
local DOORS = {
	KRM_DOOR_08_Entrance_door_hinge_LEFT  = {h = Vector3.new( -305.0, 0.0, -4190.0), base = 0.0, open = -92.0, dur = 2.917},
	KRM_DOOR_09_Entrance_door_hinge_RIGHT = {h = Vector3.new(  305.0, 0.0, -4190.0), base = 0.0, open =  92.0, dur = 2.917},

	KRM_DOOR_04_DOOR_HINGE___Wing_portal_LEFT___A  = {h = Vector3.new(-1616.5, 0.0,  908.0), base = 0.0, open = -90.0, dur = 2.0},
	KRM_DOOR_05_DOOR_HINGE___Wing_portal_LEFT___B  = {h = Vector3.new(-1616.5, 0.0, 1232.0), base = 0.0, open =  90.0, dur = 2.0},
	KRM_DOOR_06_DOOR_HINGE___Wing_portal_RIGHT___A = {h = Vector3.new( 1616.5, 0.0, 1232.0), base = 0.0, open = -90.0, dur = 2.0},
	KRM_DOOR_07_DOOR_HINGE___Wing_portal_RIGHT___B = {h = Vector3.new( 1616.5, 0.0,  908.0), base = 0.0, open =  90.0, dur = 2.0},

	-- 윙 끝문 4짝: 소스에 키가 없다. 열고 싶으면 open 값을 채워라.
	KRM_DOOR_00_DOOR_HINGE___Wing_end_LEFT___A  = {h = Vector3.new(-2978.0, 0.0,  978.0), base = 0.0, open = -90.0, dur = 2.0},
	KRM_DOOR_01_DOOR_HINGE___Wing_end_LEFT___B  = {h = Vector3.new(-2978.0, 0.0, 1222.0), base = 0.0, open =  90.0, dur = 2.0},
	KRM_DOOR_02_DOOR_HINGE___Wing_end_RIGHT___A = {h = Vector3.new( 2978.0, 0.0, 1222.0), base = 0.0, open = -90.0, dur = 2.0},
	KRM_DOOR_03_DOOR_HINGE___Wing_end_RIGHT___B = {h = Vector3.new( 2978.0, 0.0,  978.0), base = 0.0, open =  90.0, dur = 2.0},
}

local M = {}
local state: {[string]: boolean} = {}

local function hingeCF(d): CFrame
	return CFrame.new(d.h) * CFrame.Angles(0, math.rad(d.base), 0)
end

-- 문을 특정 각도로 즉시 놓는다 (초기 배치용)
function M.set(part: BasePart, deg: number)
	local d = DOORS[part.Name]
	if not d then return end
	part.CFrame = hingeCF(d) * CFrame.Angles(0, math.rad(deg), 0)
end

-- 열기/닫기. TweenService 로 CFrame 을 보간한다.
function M.swing(part: BasePart, opened: boolean)
	local d = DOORS[part.Name]
	if not d then
		warn("[KrmDoors] 정의 없는 문: " .. part.Name)
		return
	end
	local target = hingeCF(d) * CFrame.Angles(0, math.rad(opened and d.open or 0.0), 0)
	local info = TweenInfo.new(d.dur, Enum.EasingStyle.Quad,
		opened and Enum.EasingDirection.Out or Enum.EasingDirection.In)
	TweenService:Create(part, info, {CFrame = target}):Play()
	state[part.Name] = opened
end

function M.toggle(part: BasePart)
	M.swing(part, not state[part.Name])
end

-- 짝을 이룬 두 문을 동시에
function M.swingPair(a: BasePart, b: BasePart, opened: boolean)
	M.swing(a, opened); M.swing(b, opened)
end

-- 씬의 모든 문을 닫힌 상태로 초기화
function M.initAll(root: Instance)
	for _, inst in ipairs(root:GetDescendants()) do
		if inst:IsA("BasePart") and DOORS[inst.Name] then
			inst.Anchored = true
			M.set(inst, 0.0)
			state[inst.Name] = false
		end
	end
end

M.DOORS = DOORS
return M

--[[ 사용 예 (ServerScript)

local KrmDoors = require(script.KrmDoors)
KrmDoors.initAll(workspace)

-- 정문 양쪽 동시 개방
local L = workspace:FindFirstChild("KRM_DOOR_08_Entrance_door_hinge_LEFT", true)
local R = workspace:FindFirstChild("KRM_DOOR_09_Entrance_door_hinge_RIGHT", true)
KrmDoors.swingPair(L, R, true)

-- 근접 트리거
local trigger = workspace:FindFirstChild("GateTrigger")
trigger.Touched:Connect(function(hit)
    if hit.Parent:FindFirstChild("Humanoid") then
        KrmDoors.swingPair(L, R, true)
    end
end)
]]

--[[ 검증 순서 (엔진 밖에서는 확인 불가한 것들)

1. yaw 부호 — 소스는 Blender +Z 회전, 여기서는 부호를 뒤집어 넣었다.
   문 하나를 열어 보고 벽 쪽이 아니라 방 안쪽으로 열리는지 확인할 것.
2. 정문은 옆 사파이어 기둥 때문에 93.2° 이상 못 연다 (소스에서 92°로 잡은 이유).
   기둥을 뚫고 열리면 open 값을 줄일 것.
3. UnitExtent 는 half-extent 다. 소스 치수와 비교할 때 2배 할 것.
]]
