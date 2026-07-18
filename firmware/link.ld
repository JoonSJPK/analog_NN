MEMORY {
  FLASH (rx) : ORIGIN = 0x10000000, LENGTH = 16M
  SRAM (rwx) : ORIGIN = 0x20000000, LENGTH = 264K
}
_estack = ORIGIN(SRAM) + LENGTH(SRAM);
ENTRY(reset_handler)
SECTIONS {
  .text : { KEEP(*(.vectors)) *(.text*) *(.rodata*) } > FLASH
  .data : { *(.data*) } > SRAM AT> FLASH
  .bss  : { *(.bss*) *(COMMON) } > SRAM
}
