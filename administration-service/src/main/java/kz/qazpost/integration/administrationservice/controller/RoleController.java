package kz.qazpost.integration.administrationservice.controller;

import kz.qazpost.integration.administrationservice.service.RoleService;
import kz.qazpost.integration.common.Role;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/role")
@RequiredArgsConstructor
public class RoleController {

    private final RoleService roleService;

    @GetMapping("/{page}/{size}")
    @PreAuthorize("hasAuthority('orts.admin')")
    public Page<Role> getAllRoles(@PathVariable int page,
                                  @PathVariable int size,
                                  @RequestParam(required = false) String code,
                                  @RequestParam(required = false) String desc) {
        return roleService.getAll(page, size, code, desc);
    }

    @GetMapping("/get-all")
    @PreAuthorize("hasAuthority('orts.admin')")
    public List<Role> getAllRoles(@RequestParam(required = false) String code,
                                  @RequestParam(required = false) String desc) {
        return roleService.getAll(code, desc);
    }

    @GetMapping("/{code}")
    @PreAuthorize("hasAuthority('orts.admin')")
    public Role getRoleByCode(@PathVariable String code) {
        return roleService.getByCode(code);
    }

    @PostMapping
    @PreAuthorize("hasAuthority('orts.admin')")
    public Role saveRole(@RequestBody Role role) {
        return roleService.save(role);
    }

    @PostMapping("/bind")
    @PreAuthorize("hasAuthority('orts.admin')")
    public ResponseEntity<?> bind(@RequestBody Map<String, String> body) {
        String username = body.get("username");
        String roleCode = body.get("role");
        return roleService.bind(username, roleCode);
    }

    @PostMapping("/unbind")
    @PreAuthorize("hasAuthority('orts.admin')")
    public ResponseEntity<?> unbind(@RequestBody Map<String, String> body) {
        String username = body.get("username");
        String roleCode = body.get("role");
        return roleService.unbind(username, roleCode);
    }

    @DeleteMapping("{code}")
    @PreAuthorize("hasAuthority('orts.admin')")
    public ResponseEntity<?> delete(@PathVariable String code) {
        return roleService.delete(code);
    }

}
