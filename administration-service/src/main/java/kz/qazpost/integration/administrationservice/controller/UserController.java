package kz.qazpost.integration.administrationservice.controller;

import kz.qazpost.integration.administrationservice.service.UserService;
import kz.qazpost.integration.common.User;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/user")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping("/contains/{page}/{size}")
    @PreAuthorize("hasAuthority('orts.admin')")
    public Page<User> getAllUsers(@PathVariable int page,
                                  @PathVariable int size,
                                  @RequestParam(required = false) String text) {
        return userService.getAll(page, size, text);
    }

    @GetMapping("/getUserById/{id}")
    @PreAuthorize("hasAuthority('orts.admin')")
    public User getUserById(@PathVariable Long id) {
        return userService.getById(id);
    }

    @GetMapping("/{username}")
    @PreAuthorize("hasAuthority('orts.admin')")
    public User getUserByUsername(@PathVariable String username) {
        return userService.getByUsername(username);
    }

}
