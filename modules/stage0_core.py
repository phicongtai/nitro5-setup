# -*- coding: utf-8 -*-
from modules.stage1_system import (
    SystemDiagnostics, OptimizeNetwork, UpgradeSystem,
    RpmFusionFree, RpmFusionNonFree, FlathubRepo,
    FedoraWorkstationRepos, BuildToolsDkms, AcerNitroNativeFix
)
from modules.stage2_nvidia import (
    NvidiaDriver, SwitcherooControl, EnvyControl
)
from modules.stage3_codec import (
    FullFFmpeg, GStreamerPlugins, IntelMediaDriver, PipeWireAudio
)
from modules.stage4_thermal import (
    LmSensors, ThermalD, DAMXModule
)
from modules.stage5_power import (
    TlpPowerManagement, BtrfsOptimize, FsTrimTimer,
    SwappinessConfig, IoSchedulerConfig, UsbAutosuspendFix,
    ZramOptimize
)
from modules.stage6_gnome import Fcitx5Lotus

CORE_MODULES = [
    SystemDiagnostics,
    OptimizeNetwork,
    UpgradeSystem,
    RpmFusionFree,
    RpmFusionNonFree,
    FlathubRepo,
    FedoraWorkstationRepos,
    BuildToolsDkms,
    NvidiaDriver,
    SwitcherooControl,
    EnvyControl,
    FullFFmpeg,
    GStreamerPlugins,
    IntelMediaDriver,
    PipeWireAudio,
    LmSensors,
    ThermalD,
    DAMXModule,
    TlpPowerManagement,
    BtrfsOptimize,
    FsTrimTimer,
    SwappinessConfig,
    IoSchedulerConfig,
    UsbAutosuspendFix,
    ZramOptimize,
    AcerNitroNativeFix,
    Fcitx5Lotus
]

MODULES = CORE_MODULES
