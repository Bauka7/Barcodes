package kz.qazpost.integration.administrationservice.repository;

import kz.qazpost.integration.administrationservice.entities.UserRoles;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface UserRolesRepository extends JpaRepository<UserRoles, Long> {

    List<UserRoles> findByUserId(Long userId);

}
