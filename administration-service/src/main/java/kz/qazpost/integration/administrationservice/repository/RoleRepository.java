package kz.qazpost.integration.administrationservice.repository;

import kz.qazpost.integration.administrationservice.entities.Role;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface RoleRepository extends JpaRepository<Role, String> {

    Optional<Role> findByCode(String code);

    Page<Role> findByCodeContainingIgnoreCaseOrDescriptionContainingIgnoreCase(String code, String desc, Pageable pageable);

    List<Role> findByCodeContainingIgnoreCaseOrDescriptionContainingIgnoreCase(String code, String desc);

    @Query("""
                select distinct r
                from UserRoles u
                join Role r on r.code = u.roleCode
                where u.userId = :userId
            """)
    List<Role> findAllByUserId(@Param("userId") Long userId);

}
